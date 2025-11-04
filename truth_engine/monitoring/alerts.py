"""
Alert System - Triggers and manages alerts for system monitoring.
Integrates with metrics to detect issues and notify operators.
"""

import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class Alert:
    """Represents a system alert."""
    id: str
    alert_type: str
    severity: AlertSeverity
    status: AlertStatus
    title: str
    description: str
    trigger_metric: str
    trigger_threshold: float
    actual_value: float
    metadata: Dict
    triggered_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "alert_type": self.alert_type,
            "severity": self.severity.value,
            "status": self.status.value,
            "title": self.title,
            "description": self.description,
            "trigger_metric": self.trigger_metric,
            "trigger_threshold": self.trigger_threshold,
            "actual_value": self.actual_value,
            "metadata": self.metadata,
            "triggered_at": self.triggered_at.isoformat(),
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "acknowledged_by": self.acknowledged_by,
            "resolved_by": self.resolved_by
        }


class AlertRule:
    """Defines a rule for triggering alerts."""

    def __init__(
        self,
        name: str,
        alert_type: str,
        severity: AlertSeverity,
        condition: Callable,
        title_template: str,
        description_template: str,
        cooldown_minutes: int = 60
    ):
        """
        Initialize alert rule.

        Args:
            name: Rule name
            alert_type: Type of alert
            severity: Alert severity
            condition: Function that returns (triggered: bool, metrics: dict)
            title_template: Title template (can use {metric_name} placeholders)
            description_template: Description template
            cooldown_minutes: Minimum time between alerts of this type
        """
        self.name = name
        self.alert_type = alert_type
        self.severity = severity
        self.condition = condition
        self.title_template = title_template
        self.description_template = description_template
        self.cooldown_minutes = cooldown_minutes
        self.last_triggered = None

    def check(self, context: Dict) -> Optional[Alert]:
        """
        Check if alert should be triggered.

        Args:
            context: Context dictionary with metrics

        Returns:
            Alert object if triggered, None otherwise
        """
        # Check cooldown
        if self.last_triggered:
            time_since_last = datetime.utcnow() - self.last_triggered
            if time_since_last < timedelta(minutes=self.cooldown_minutes):
                return None

        # Evaluate condition
        triggered, metrics = self.condition(context)

        if not triggered:
            return None

        # Create alert
        alert = Alert(
            id=str(uuid.uuid4()),
            alert_type=self.alert_type,
            severity=self.severity,
            status=AlertStatus.ACTIVE,
            title=self.title_template.format(**metrics),
            description=self.description_template.format(**metrics),
            trigger_metric=metrics.get("metric_name", "unknown"),
            trigger_threshold=metrics.get("threshold", 0.0),
            actual_value=metrics.get("actual_value", 0.0),
            metadata=metrics,
            triggered_at=datetime.utcnow()
        )

        self.last_triggered = datetime.utcnow()
        logger.warning(f"Alert triggered: {alert.title}")

        return alert


class AlertManager:
    """
    Manages alerts and notification channels.

    Features:
    - Rule-based alert triggering
    - Alert deduplication
    - Status management (acknowledge, resolve)
    - Notification routing
    """

    def __init__(self):
        """Initialize alert manager."""
        self.rules: List[AlertRule] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_handlers: List[Callable] = []

        # Register default rules
        self._register_default_rules()

        logger.info("AlertManager initialized")

    def _register_default_rules(self):
        """Register default alert rules."""

        # Rule 1: Truth score degradation
        def check_score_degradation(context: Dict) -> tuple:
            degradation = context.get("degradation_details")
            if degradation:
                return True, {
                    "metric_name": "truth_score",
                    "threshold": degradation["threshold"],
                    "actual_value": degradation["recent_avg"],
                    "baseline": degradation["baseline_avg"],
                    "degradation": degradation["degradation"]
                }
            return False, {}

        self.add_rule(AlertRule(
            name="truth_score_degradation",
            alert_type="score_degradation",
            severity=AlertSeverity.WARNING,
            condition=check_score_degradation,
            title_template="Truth Score Degraded by {degradation:.1%}",
            description_template=(
                "Truth scores have degraded significantly. "
                "Baseline average: {baseline:.3f}, Recent average: {actual_value:.3f}. "
                "Degradation: {degradation:.3f} (threshold: {threshold:.3f})"
            ),
            cooldown_minutes=30
        ))

        # Rule 2: High error rate
        def check_error_rate(context: Dict) -> tuple:
            error_rate = context.get("error_rate", 0.0)
            threshold = context.get("error_rate_threshold", 0.1)
            if error_rate > threshold:
                return True, {
                    "metric_name": "error_rate",
                    "threshold": threshold,
                    "actual_value": error_rate
                }
            return False, {}

        self.add_rule(AlertRule(
            name="high_error_rate",
            alert_type="high_error_rate",
            severity=AlertSeverity.ERROR,
            condition=check_error_rate,
            title_template="High Error Rate: {actual_value:.1%}",
            description_template=(
                "Error rate has exceeded threshold. "
                "Current: {actual_value:.1%}, Threshold: {threshold:.1%}"
            ),
            cooldown_minutes=15
        ))

        # Rule 3: Low verification rate
        def check_verification_rate(context: Dict) -> tuple:
            verification_rate = context.get("verification_rate", 1.0)
            threshold = context.get("min_verification_rate", 0.5)
            if verification_rate < threshold:
                return True, {
                    "metric_name": "verification_rate",
                    "threshold": threshold,
                    "actual_value": verification_rate
                }
            return False, {}

        self.add_rule(AlertRule(
            name="low_verification_rate",
            alert_type="low_verification_rate",
            severity=AlertSeverity.WARNING,
            condition=check_verification_rate,
            title_template="Low Verification Rate: {actual_value:.1%}",
            description_template=(
                "Verification rate is below acceptable threshold. "
                "Current: {actual_value:.1%}, Minimum: {threshold:.1%}"
            ),
            cooldown_minutes=60
        ))

        # Rule 4: High contradiction rate
        def check_contradiction_rate(context: Dict) -> tuple:
            contradiction_rate = context.get("contradiction_rate", 0.0)
            threshold = context.get("max_contradiction_rate", 0.3)
            if contradiction_rate > threshold:
                return True, {
                    "metric_name": "contradiction_rate",
                    "threshold": threshold,
                    "actual_value": contradiction_rate
                }
            return False, {}

        self.add_rule(AlertRule(
            name="high_contradiction_rate",
            alert_type="high_contradiction_rate",
            severity=AlertSeverity.WARNING,
            condition=check_contradiction_rate,
            title_template="High Contradiction Rate: {actual_value:.1%}",
            description_template=(
                "Too many claims are being contradicted. "
                "Current: {actual_value:.1%}, Maximum: {threshold:.1%}"
            ),
            cooldown_minutes=30
        ))

        # Rule 5: Slow processing
        def check_processing_time(context: Dict) -> tuple:
            avg_time = context.get("avg_processing_time_ms", 0.0)
            threshold = context.get("max_processing_time_ms", 5000.0)
            if avg_time > threshold:
                return True, {
                    "metric_name": "processing_time",
                    "threshold": threshold,
                    "actual_value": avg_time
                }
            return False, {}

        self.add_rule(AlertRule(
            name="slow_processing",
            alert_type="performance_degradation",
            severity=AlertSeverity.WARNING,
            condition=check_processing_time,
            title_template="Slow Processing: {actual_value:.0f}ms",
            description_template=(
                "Average processing time exceeds threshold. "
                "Current: {actual_value:.0f}ms, Maximum: {threshold:.0f}ms"
            ),
            cooldown_minutes=20
        ))

    def add_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self.rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")

    def add_notification_handler(self, handler: Callable):
        """
        Add a notification handler.

        Handler should accept an Alert object.
        """
        self.notification_handlers.append(handler)
        logger.info(f"Added notification handler: {handler.__name__}")

    def check_all_rules(self, context: Dict) -> List[Alert]:
        """
        Check all rules and trigger alerts.

        Args:
            context: Context dictionary with current metrics

        Returns:
            List of newly triggered alerts
        """
        new_alerts = []

        for rule in self.rules:
            try:
                alert = rule.check(context)
                if alert:
                    self.active_alerts[alert.id] = alert
                    self.alert_history.append(alert)
                    new_alerts.append(alert)

                    # Send notifications
                    self._send_notifications(alert)

            except Exception as e:
                logger.error(f"Error checking rule {rule.name}: {e}")

        return new_alerts

    def _send_notifications(self, alert: Alert):
        """Send notifications for an alert."""
        for handler in self.notification_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in notification handler: {e}")

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Acknowledge an active alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = acknowledged_by
            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")

    def resolve_alert(self, alert_id: str, resolved_by: str):
        """Resolve an active alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by = resolved_by
            del self.active_alerts[alert_id]
            logger.info(f"Alert {alert_id} resolved by {resolved_by}")

    def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """
        Get all active alerts, optionally filtered by severity.

        Args:
            severity: Optional severity filter

        Returns:
            List of active alerts
        """
        alerts = list(self.active_alerts.values())

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        # Sort by severity (critical first) then by time
        severity_order = {
            AlertSeverity.CRITICAL: 0,
            AlertSeverity.ERROR: 1,
            AlertSeverity.WARNING: 2,
            AlertSeverity.INFO: 3
        }

        alerts.sort(key=lambda a: (severity_order[a.severity], a.triggered_at))

        return alerts

    def get_alert_summary(self) -> Dict:
        """Get summary of alert status."""
        active = self.get_active_alerts()

        return {
            "total_active": len(active),
            "by_severity": {
                "critical": len([a for a in active if a.severity == AlertSeverity.CRITICAL]),
                "error": len([a for a in active if a.severity == AlertSeverity.ERROR]),
                "warning": len([a for a in active if a.severity == AlertSeverity.WARNING]),
                "info": len([a for a in active if a.severity == AlertSeverity.INFO])
            },
            "total_history": len(self.alert_history),
            "recent_alerts": [a.to_dict() for a in active[:5]]
        }


# Default notification handlers

def console_notification_handler(alert: Alert):
    """Print alert to console."""
    severity_icons = {
        AlertSeverity.CRITICAL: "🔴",
        AlertSeverity.ERROR: "🟠",
        AlertSeverity.WARNING: "🟡",
        AlertSeverity.INFO: "🔵"
    }

    icon = severity_icons.get(alert.severity, "⚪")
    print(f"\n{icon} ALERT [{alert.severity.value.upper()}]: {alert.title}")
    print(f"   {alert.description}")
    print(f"   Triggered at: {alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}")


def log_notification_handler(alert: Alert):
    """Log alert."""
    level_map = {
        AlertSeverity.CRITICAL: logging.CRITICAL,
        AlertSeverity.ERROR: logging.ERROR,
        AlertSeverity.WARNING: logging.WARNING,
        AlertSeverity.INFO: logging.INFO
    }

    level = level_map.get(alert.severity, logging.WARNING)
    logger.log(level, f"Alert: {alert.title} - {alert.description}")


def main():
    """Example usage of AlertManager."""
    manager = AlertManager()

    # Add notification handlers
    manager.add_notification_handler(console_notification_handler)
    manager.add_notification_handler(log_notification_handler)

    # Simulate metrics context with issues
    print("Simulating monitoring with various issues...\n")

    contexts = [
        {
            "name": "Score Degradation",
            "degradation_details": {
                "threshold": 0.1,
                "baseline_avg": 0.75,
                "recent_avg": 0.60,
                "degradation": 0.15
            }
        },
        {
            "name": "High Error Rate",
            "error_rate": 0.15,
            "error_rate_threshold": 0.1
        },
        {
            "name": "Low Verification",
            "verification_rate": 0.35,
            "min_verification_rate": 0.5
        },
        {
            "name": "Slow Processing",
            "avg_processing_time_ms": 6500,
            "max_processing_time_ms": 5000
        }
    ]

    for context in contexts:
        print(f"\n{'='*60}")
        print(f"Context: {context['name']}")
        print('='*60)
        alerts = manager.check_all_rules(context)
        if not alerts:
            print("No alerts triggered.")

    # Show summary
    print(f"\n{'='*60}")
    print("Alert Summary")
    print('='*60)
    summary = manager.get_alert_summary()
    print(f"Total Active Alerts: {summary['total_active']}")
    print(f"By Severity: {summary['by_severity']}")


if __name__ == "__main__":
    main()
