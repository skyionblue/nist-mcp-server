"""Continuous monitoring system for NIST controls

Provides automated periodic checks for key controls with connector integration.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
import logging

from ..history.storage import HistoricalStorage

logger = logging.getLogger(__name__)


class ControlMonitor:
    """Continuous monitoring system for NIST controls"""

    def __init__(self, storage: HistoricalStorage):
        self.storage = storage
        self.monitored_controls: Dict[str, Dict[str, Any]] = {}
        self.schedules: Dict[str, asyncio.Task] = {}
        self.connectors: Dict[str, Any] = {}  # Will hold connector instances

    def register_connector(self, connector_id: str, connector_instance: Any) -> None:
        """Register a connector for monitoring checks"""
        self.connectors[connector_id] = connector_instance
        logger.info(f"Registered connector {connector_id}")

    def start_monitoring_control(
        self,
        control_id: str,
        check_interval_hours: int = 24,
        connector_id: Optional[str] = None,
        check_type: str = "automated",
        custom_check_function: Optional[Callable] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Start monitoring a specific control"""
        # A non-positive interval makes _monitor_loop schedule the next check in the
        # past and sleep for <= 0, producing a tight CPU/storage loop.
        if check_interval_hours <= 0:
            raise ValueError(
                f"check_interval_hours must be positive, got {check_interval_hours}"
            )

        # Second-precision ids collide when the same control is started twice within a
        # second: the schedules entry is overwritten and the first task leaks.
        monitor_id = f"monitor_{control_id}_{uuid.uuid4().hex}"

        self.monitored_controls[monitor_id] = {
            "control_id": control_id,
            "interval_hours": check_interval_hours,
            "connector_id": connector_id,
            "check_type": check_type,
            "custom_check_function": custom_check_function,
            "parameters": parameters or {},
            "next_check": datetime.now(),
            "status": "active",
        }

        # Start the monitoring task
        task = asyncio.create_task(self._monitor_loop(monitor_id))
        self.schedules[monitor_id] = task

        logger.info(
            f"Started monitoring for control {control_id} every {check_interval_hours} hours"
        )
        return monitor_id

    async def shutdown(self) -> None:
        """Cancel and await every scheduled monitoring task.

        The container's shutdown loop only calls `shutdown` if it exists; without this
        every _monitor_loop kept running after the server shut down.
        """
        tasks = list(self.schedules.values())
        for task in tasks:
            task.cancel()
        for task in tasks:
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
        self.schedules.clear()
        self.monitored_controls.clear()
        logger.info("Control monitor shut down; %d task(s) cancelled", len(tasks))

    def stop_monitoring(self, monitor_id: str) -> bool:
        """Stop monitoring a control"""
        if monitor_id in self.schedules:
            self.schedules[monitor_id].cancel()
            del self.schedules[monitor_id]

        if monitor_id in self.monitored_controls:
            self.monitored_controls[monitor_id]["status"] = "stopped"
            return True

        return False

    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            "active_monitors": len(
                [m for m in self.monitored_controls.values() if m["status"] == "active"]
            ),
            "monitored_controls": [
                {
                    "monitor_id": mid,
                    "control_id": config["control_id"],
                    "interval_hours": config["interval_hours"],
                    "next_check": config["next_check"].isoformat(),
                    "status": config["status"],
                }
                for mid, config in self.monitored_controls.items()
            ],
            "total_scheduled_tasks": len(self.schedules),
        }

    async def run_immediate_check(
        self, control_id: str, connector_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run an immediate check for a control"""
        monitor_config = {
            "control_id": control_id,
            "connector_id": connector_id,
            "check_type": "manual",
            "parameters": {},
        }

        return await self._perform_check(monitor_config)

    async def _monitor_loop(self, monitor_id: str) -> None:
        """Main monitoring loop for a control"""
        try:
            while (
                monitor_id in self.monitored_controls
                and self.monitored_controls[monitor_id]["status"] == "active"
            ):
                config = self.monitored_controls[monitor_id]
                now = datetime.now()

                if now >= config["next_check"]:
                    # Perform the check
                    result = await self._perform_check(config)

                    # Schedule next check
                    config["next_check"] = now + timedelta(
                        hours=config["interval_hours"]
                    )

                    # Log the check in history
                    self.storage.record_monitoring_check(
                        {
                            "control_id": config["control_id"],
                            "check_type": config["check_type"],
                            "connector_id": config["connector_id"],
                            "status": result["status"],
                            "result_details": result,
                            "evidence_paths": result.get("evidence_paths", []),
                            "next_check_scheduled": config["next_check"],
                        }
                    )

                # Wait for next check or until monitoring is stopped
                await asyncio.sleep(
                    min(60, (config["next_check"] - datetime.now()).total_seconds())
                )

        except asyncio.CancelledError:
            logger.info(f"Monitoring cancelled for {monitor_id}")
        except Exception as e:
            logger.error(f"Error in monitoring loop for {monitor_id}: {e}")

    async def _perform_check(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a control check"""
        control_id = config["control_id"]
        connector_id = config.get("connector_id")
        check_type = config.get("check_type", "automated")
        custom_function = config.get("custom_check_function")
        parameters = config.get("parameters", {})

        try:
            if custom_function:
                # Use custom check function
                result = await custom_function(control_id, **parameters)
            elif connector_id and connector_id in self.connectors:
                # Use registered connector
                connector = self.connectors[connector_id]
                result = await connector.check_control(control_id, parameters)
            else:
                # Default check (basic implementation status check)
                result = await self._default_control_check(control_id, parameters)

            return result

        except Exception as e:
            logger.error(f"Error checking control {control_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "control_id": control_id,
                "check_type": check_type,
            }

    async def _default_control_check(
        self, control_id: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback used when a monitor has no connector registered.

        There is no way to determine a control's status without a connector, so this
        reports ``unknown`` rather than guessing. It previously returned randomised
        pass/fail/warning values with randomised confidence scores, which meant
        monitoring could emit compliance findings unrelated to any real system state.
        """
        return {
            "status": "unknown",
            "confidence": 0.0,
            "timestamp": datetime.now().isoformat(),
            "control_id": control_id,
            "message": (
                f"No connector registered for {control_id}; status cannot be "
                f"determined. Register a connector that implements a real check."
            ),
            "evidence_paths": [],
            "details": {
                "check_method": "no_connector",
                "parameters_used": parameters,
                "confidence_score": 0.0,
            },
        }

    def get_control_monitoring_history(
        self, control_id: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get monitoring history for a specific control"""
        return self.storage.get_monitoring_history(control_id=control_id, days=days)

    def get_all_monitoring_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get all monitoring check history"""
        return self.storage.get_monitoring_history(days=days)
