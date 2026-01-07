"""
Due Diligence Timeline Tracker.

Tracks critical deadlines and orchestrates due diligence workflow.
Generates action sequences and delegates tasks to appropriate specialists.
"""

from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "N/A"


class UrgencyLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    NORMAL = "NORMAL"
    LOW = "LOW"


@dataclass
class Deadline:
    """A critical deadline in the due diligence process."""
    name: str
    date: date
    days_remaining: int
    urgency: UrgencyLevel
    action: str
    condition_type: Optional[str] = None
    completed: bool = False
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "date": self.date.isoformat(),
            "days_remaining": self.days_remaining,
            "urgency": self.urgency.value,
            "action": self.action,
            "condition_type": self.condition_type,
            "completed": self.completed,
            "notes": self.notes
        }


@dataclass
class DelegatedTask:
    """A task to be delegated to a specialist."""
    task: str
    delegate_to: str
    deadline: date
    status: TaskStatus
    estimated_cost: Optional[str] = None
    applies_if: Optional[str] = None
    priority: int = 1
    contact_info: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "delegate_to": self.delegate_to,
            "deadline": self.deadline.isoformat(),
            "status": self.status.value,
            "estimated_cost": self.estimated_cost,
            "applies_if": self.applies_if,
            "priority": self.priority,
            "contact_info": self.contact_info,
            "notes": self.notes
        }


@dataclass
class ActionItem:
    """A recommended action item with timing."""
    action: str
    timing: str
    priority: int
    category: str
    estimated_duration: str
    dependencies: List[str] = field(default_factory=list)
    completed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "timing": self.timing,
            "priority": self.priority,
            "category": self.category,
            "estimated_duration": self.estimated_duration,
            "dependencies": self.dependencies,
            "completed": self.completed
        }


@dataclass
class TimelineResult:
    """Complete timeline result."""
    property_id: Optional[str]
    contract_signed: date
    cooling_off_expires: Optional[date]
    settlement_date: date
    critical_deadlines: List[Deadline] = field(default_factory=list)
    recommended_actions: List[ActionItem] = field(default_factory=list)
    delegated_tasks: List[DelegatedTask] = field(default_factory=list)
    days_to_settlement: int = 0
    overall_status: str = "ON_TRACK"
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "property_id": self.property_id,
            "contract_signed": self.contract_signed.isoformat(),
            "cooling_off_expires": self.cooling_off_expires.isoformat() if self.cooling_off_expires else None,
            "settlement_date": self.settlement_date.isoformat(),
            "critical_deadlines": [d.to_dict() for d in self.critical_deadlines],
            "recommended_actions": [a.to_dict() for a in self.recommended_actions],
            "delegated_tasks": [t.to_dict() for t in self.delegated_tasks],
            "days_to_settlement": self.days_to_settlement,
            "overall_status": self.overall_status,
            "warnings": self.warnings
        }


class DueDiligenceTimeline:
    """
    Tracks critical deadlines and orchestrates due diligence workflow.

    Key features:
    - Tracks cooling-off, finance, building inspection, and settlement deadlines
    - Generates recommended action sequences
    - Creates delegated task lists with appropriate specialists
    - Monitors overall progress and flags risks
    """

    def create_timeline(
        self,
        contract_signed_date: date,
        cooling_off_expires: Optional[date],
        settlement_date: date,
        special_conditions: List[Dict[str, Any]],
        property_type: str = "house",
        property_id: Optional[str] = None,
        is_investment: bool = False
    ) -> TimelineResult:
        """
        Create a comprehensive due diligence timeline.

        Args:
            contract_signed_date: Date the contract was signed
            cooling_off_expires: Cooling-off expiry date (None if exempt)
            settlement_date: Settlement date
            special_conditions: List of special conditions with type, deadline, etc.
            property_type: Type of property (house, apartment, townhouse, unit)
            property_id: Optional property identifier
            is_investment: Whether this is an investment purchase

        Returns:
            TimelineResult with all deadlines, actions, and tasks
        """
        today = date.today()
        result = TimelineResult(
            property_id=property_id,
            contract_signed=contract_signed_date,
            cooling_off_expires=cooling_off_expires,
            settlement_date=settlement_date,
            days_to_settlement=(settlement_date - today).days
        )

        # Build critical deadlines
        result.critical_deadlines = self._build_critical_deadlines(
            today=today,
            cooling_off_expires=cooling_off_expires,
            settlement_date=settlement_date,
            special_conditions=special_conditions
        )

        # Generate recommended actions
        result.recommended_actions = self._generate_action_sequence(
            today=today,
            cooling_off_expires=cooling_off_expires,
            settlement_date=settlement_date,
            special_conditions=special_conditions,
            property_type=property_type,
            is_investment=is_investment
        )

        # Create delegated tasks
        result.delegated_tasks = self._create_delegated_tasks(
            cooling_off_expires=cooling_off_expires,
            settlement_date=settlement_date,
            special_conditions=special_conditions,
            property_type=property_type,
            is_investment=is_investment
        )

        # Determine overall status and warnings
        result.overall_status, result.warnings = self._assess_timeline_status(
            result.critical_deadlines, today
        )

        return result

    def _build_critical_deadlines(
        self,
        today: date,
        cooling_off_expires: Optional[date],
        settlement_date: date,
        special_conditions: List[Dict[str, Any]]
    ) -> List[Deadline]:
        """Build list of critical deadlines from contract details."""
        deadlines = []

        # Cooling-off deadline (most urgent)
        if cooling_off_expires:
            days_to_cooling_off = (cooling_off_expires - today).days
            urgency = UrgencyLevel.CRITICAL if days_to_cooling_off <= 1 else (
                UrgencyLevel.HIGH if days_to_cooling_off <= 2 else UrgencyLevel.MEDIUM
            )
            deadlines.append(Deadline(
                name="Cooling-Off Expires",
                date=cooling_off_expires,
                days_remaining=days_to_cooling_off,
                urgency=urgency,
                action="Complete all critical due diligence before this date. "
                       "Building inspection and Section 32 review must be finalized.",
                condition_type="cooling_off",
                notes="After this date, contract is binding (subject to special conditions)"
            ))

        # Finance approval deadline
        finance_condition = next(
            (c for c in special_conditions if c.get("type") in ["subject_to_finance", "finance"]),
            None
        )
        if finance_condition:
            finance_deadline = self._parse_deadline(finance_condition.get("deadline"))
            if finance_deadline:
                days_remaining = (finance_deadline - today).days
                urgency = self._get_urgency_level(days_remaining)
                deadlines.append(Deadline(
                    name="Finance Approval Due",
                    date=finance_deadline,
                    days_remaining=days_remaining,
                    urgency=urgency,
                    action="Obtain formal loan approval or invoke condition to exit contract",
                    condition_type="subject_to_finance",
                    notes="Lender must issue unconditional approval by this date"
                ))

        # Building inspection deadline
        building_condition = next(
            (c for c in special_conditions
             if c.get("type") in ["subject_to_building_inspection", "building_inspection", "building_and_pest"]),
            None
        )
        if building_condition:
            building_deadline = self._parse_deadline(building_condition.get("deadline"))
            if building_deadline:
                days_remaining = (building_deadline - today).days
                urgency = self._get_urgency_level(days_remaining)
                deadlines.append(Deadline(
                    name="Building Inspection Due",
                    date=building_deadline,
                    days_remaining=days_remaining,
                    urgency=urgency,
                    action="Complete building inspection, review report, and negotiate repairs if needed",
                    condition_type="subject_to_building_inspection",
                    notes="Book inspector ASAP - busy periods can have 3-5 day wait times"
                ))

        # Pest inspection deadline (if separate)
        pest_condition = next(
            (c for c in special_conditions
             if c.get("type") in ["subject_to_pest_inspection", "pest_inspection"]),
            None
        )
        if pest_condition:
            pest_deadline = self._parse_deadline(pest_condition.get("deadline"))
            if pest_deadline:
                days_remaining = (pest_deadline - today).days
                urgency = self._get_urgency_level(days_remaining)
                deadlines.append(Deadline(
                    name="Pest Inspection Due",
                    date=pest_deadline,
                    days_remaining=days_remaining,
                    urgency=urgency,
                    action="Complete pest inspection and review report",
                    condition_type="subject_to_pest_inspection"
                ))

        # Strata inspection deadline (if applicable)
        strata_condition = next(
            (c for c in special_conditions
             if c.get("type") in ["subject_to_strata", "strata_inspection"]),
            None
        )
        if strata_condition:
            strata_deadline = self._parse_deadline(strata_condition.get("deadline"))
            if strata_deadline:
                days_remaining = (strata_deadline - today).days
                urgency = self._get_urgency_level(days_remaining)
                deadlines.append(Deadline(
                    name="Strata Inspection Due",
                    date=strata_deadline,
                    days_remaining=days_remaining,
                    urgency=urgency,
                    action="Review Section 151 certificate, AGM minutes, and financial statements",
                    condition_type="subject_to_strata"
                ))

        # Settlement
        days_to_settlement = (settlement_date - today).days
        settlement_urgency = UrgencyLevel.HIGH if days_to_settlement <= 14 else (
            UrgencyLevel.MEDIUM if days_to_settlement <= 30 else UrgencyLevel.NORMAL
        )
        deadlines.append(Deadline(
            name="Settlement",
            date=settlement_date,
            days_remaining=days_to_settlement,
            urgency=settlement_urgency,
            action="Transfer of ownership, payment of balance, and handover of keys",
            condition_type="settlement",
            notes="Ensure all funds are available and conveyancer is prepared"
        ))

        # Sort by date
        deadlines.sort(key=lambda d: d.date)

        return deadlines

    def _parse_deadline(self, deadline_value: Any) -> Optional[date]:
        """Parse deadline from various formats."""
        if deadline_value is None:
            return None
        if isinstance(deadline_value, date):
            return deadline_value
        if isinstance(deadline_value, datetime):
            return deadline_value.date()
        if isinstance(deadline_value, str):
            try:
                return date.fromisoformat(deadline_value)
            except ValueError:
                return None
        return None

    def _get_urgency_level(self, days_remaining: int) -> UrgencyLevel:
        """Determine urgency level based on days remaining."""
        if days_remaining < 0:
            return UrgencyLevel.CRITICAL  # Overdue
        if days_remaining <= 1:
            return UrgencyLevel.CRITICAL
        if days_remaining <= 3:
            return UrgencyLevel.HIGH
        if days_remaining <= 7:
            return UrgencyLevel.MEDIUM
        return UrgencyLevel.NORMAL

    def _generate_action_sequence(
        self,
        today: date,
        cooling_off_expires: Optional[date],
        settlement_date: date,
        special_conditions: List[Dict[str, Any]],
        property_type: str,
        is_investment: bool
    ) -> List[ActionItem]:
        """Generate recommended action sequence based on deadlines."""
        actions = []

        # Immediate actions (Day 1)
        actions.append(ActionItem(
            action="Engage conveyancer/solicitor for contract review",
            timing="Immediately (Day 1)",
            priority=1,
            category="Legal",
            estimated_duration="1-2 hours to brief",
            dependencies=[]
        ))

        actions.append(ActionItem(
            action="Review Section 32 Vendor Statement for completeness",
            timing="Day 1",
            priority=1,
            category="Legal",
            estimated_duration="30 minutes with conveyancer",
            dependencies=[]
        ))

        actions.append(ActionItem(
            action="Book building and pest inspection",
            timing="Day 1",
            priority=1,
            category="Physical",
            estimated_duration="10 minutes to book, 2-3 hours for inspection",
            dependencies=[]
        ))

        # Day 2 actions
        actions.append(ActionItem(
            action="Submit finance application to lender",
            timing="Day 1-2",
            priority=1,
            category="Financial",
            estimated_duration="1-2 hours with broker",
            dependencies=["Pre-approval in place"]
        ))

        actions.append(ActionItem(
            action="Review title search for encumbrances",
            timing="Day 2",
            priority=2,
            category="Legal",
            estimated_duration="20 minutes",
            dependencies=["Section 32 received"]
        ))

        # Strata-specific actions
        if property_type in ["apartment", "townhouse", "unit"]:
            actions.append(ActionItem(
                action="Order Section 151 Owners Corporation Certificate",
                timing="Day 1-2",
                priority=1,
                category="Strata",
                estimated_duration="5-10 business days for delivery",
                dependencies=[]
            ))

            actions.append(ActionItem(
                action="Review AGM minutes for cladding, special levies, litigation",
                timing="Days 2-3",
                priority=1,
                category="Strata",
                estimated_duration="1-2 hours",
                dependencies=["OC Certificate received"]
            ))

            actions.append(ActionItem(
                action="Analyze strata financial health (sinking fund, admin fund)",
                timing="Days 2-3",
                priority=2,
                category="Strata",
                estimated_duration="30 minutes",
                dependencies=["Financial statements received"]
            ))

        # Day 3 actions
        actions.append(ActionItem(
            action="Attend building inspection (recommended)",
            timing="Day 2-3",
            priority=2,
            category="Physical",
            estimated_duration="2-3 hours",
            dependencies=["Inspection booked"]
        ))

        actions.append(ActionItem(
            action="Review building inspection report",
            timing="Day 3",
            priority=1,
            category="Physical",
            estimated_duration="30-60 minutes",
            dependencies=["Inspection completed"]
        ))

        # Before cooling-off expires
        if cooling_off_expires:
            actions.append(ActionItem(
                action="Make final decision: proceed or exercise cooling-off rights",
                timing=f"Before {cooling_off_expires.strftime('%d %B')} (cooling-off)",
                priority=1,
                category="Decision",
                estimated_duration="Discussion with all stakeholders",
                dependencies=["Building report reviewed", "Section 32 reviewed", "Finance status confirmed"]
            ))

        # Week 2 actions
        actions.append(ActionItem(
            action="Follow up on finance approval status",
            timing="Week 2",
            priority=1,
            category="Financial",
            estimated_duration="Phone call to broker",
            dependencies=["Finance application submitted"]
        ))

        actions.append(ActionItem(
            action="Review planning overlays and permitted uses",
            timing="Week 2",
            priority=3,
            category="Planning",
            estimated_duration="1 hour",
            dependencies=[]
        ))

        # Investment-specific actions
        if is_investment:
            actions.append(ActionItem(
                action="Order depreciation schedule (quantity surveyor)",
                timing="Week 2",
                priority=3,
                category="Financial",
                estimated_duration="2-3 weeks for report",
                dependencies=[]
            ))

            actions.append(ActionItem(
                action="Conduct rental appraisal",
                timing="Week 2",
                priority=2,
                category="Financial",
                estimated_duration="Property manager visit",
                dependencies=[]
            ))

        # Pre-settlement actions
        actions.append(ActionItem(
            action="Confirm unconditional finance approval",
            timing="Before finance deadline",
            priority=1,
            category="Financial",
            estimated_duration="Broker confirmation",
            dependencies=["Valuation completed", "All lender conditions met"]
        ))

        actions.append(ActionItem(
            action="Arrange building insurance from settlement date",
            timing="1 week before settlement",
            priority=1,
            category="Insurance",
            estimated_duration="30 minutes",
            dependencies=[]
        ))

        actions.append(ActionItem(
            action="Final property inspection (pre-settlement)",
            timing="1-2 days before settlement",
            priority=1,
            category="Physical",
            estimated_duration="30-60 minutes",
            dependencies=[]
        ))

        actions.append(ActionItem(
            action="Ensure settlement funds are ready",
            timing="Day before settlement",
            priority=1,
            category="Financial",
            estimated_duration="Bank confirmation",
            dependencies=["Finance approved"]
        ))

        return actions

    def _create_delegated_tasks(
        self,
        cooling_off_expires: Optional[date],
        settlement_date: date,
        special_conditions: List[Dict[str, Any]],
        property_type: str,
        is_investment: bool
    ) -> List[DelegatedTask]:
        """Create list of tasks to delegate to specialists."""
        tasks = []

        # Get condition deadlines
        finance_condition = next(
            (c for c in special_conditions if c.get("type") in ["subject_to_finance", "finance"]),
            None
        )
        building_condition = next(
            (c for c in special_conditions
             if c.get("type") in ["subject_to_building_inspection", "building_inspection", "building_and_pest"]),
            None
        )

        # Conveyancer tasks
        tasks.append(DelegatedTask(
            task="Contract review and advice",
            delegate_to="Conveyancer/Solicitor",
            deadline=cooling_off_expires or (settlement_date - timedelta(days=30)),
            status=TaskStatus.PENDING,
            estimated_cost="$1,200 - $2,500 (full conveyancing)",
            priority=1,
            notes="Should review within 24 hours of signing"
        ))

        tasks.append(DelegatedTask(
            task="Title and encumbrance searches",
            delegate_to="Conveyancer/Solicitor",
            deadline=cooling_off_expires or (settlement_date - timedelta(days=21)),
            status=TaskStatus.PENDING,
            estimated_cost="Included in conveyancing fee",
            priority=1
        ))

        # Building inspector
        building_deadline = self._parse_deadline(building_condition.get("deadline")) if building_condition else None
        tasks.append(DelegatedTask(
            task="Building and pest inspection",
            delegate_to="Registered Building Inspector",
            deadline=building_deadline or (settlement_date - timedelta(days=21)),
            status=TaskStatus.PENDING,
            estimated_cost="$400 - $800",
            priority=1,
            notes="Book immediately - busy periods can have 3-5 day wait"
        ))

        # Mortgage broker
        finance_deadline = self._parse_deadline(finance_condition.get("deadline")) if finance_condition else None
        tasks.append(DelegatedTask(
            task="Finance application and approval",
            delegate_to="Mortgage Broker",
            deadline=finance_deadline or (settlement_date - timedelta(days=21)),
            status=TaskStatus.PENDING,
            estimated_cost="Typically paid by lender",
            priority=1
        ))

        # Strata-specific tasks
        if property_type in ["apartment", "townhouse", "unit"]:
            tasks.append(DelegatedTask(
                task="Strata search (Section 151 certificate)",
                delegate_to="Conveyancer or Strata Search Company",
                deadline=cooling_off_expires or (settlement_date - timedelta(days=21)),
                status=TaskStatus.PENDING,
                estimated_cost="$175 - $330",
                applies_if="property_type IN ['apartment', 'townhouse', 'unit']",
                priority=1,
                notes="Critical for discovering special levies, litigation, cladding issues"
            ))

        # Investment-specific tasks
        if is_investment:
            tasks.append(DelegatedTask(
                task="Depreciation schedule",
                delegate_to="Quantity Surveyor",
                deadline=settlement_date + timedelta(days=30),  # Can be done post-settlement
                status=TaskStatus.PENDING,
                estimated_cost="$500 - $800",
                applies_if="investment_property",
                priority=3,
                notes="Tax benefit typically $5,000-15,000+ over holding period"
            ))

            tasks.append(DelegatedTask(
                task="Rental appraisal",
                delegate_to="Property Manager",
                deadline=settlement_date - timedelta(days=7),
                status=TaskStatus.PENDING,
                estimated_cost="Usually free",
                applies_if="investment_property",
                priority=2
            ))

        # Insurance
        tasks.append(DelegatedTask(
            task="Building insurance quote and arrangement",
            delegate_to="Insurance Broker",
            deadline=settlement_date - timedelta(days=7),
            status=TaskStatus.PENDING,
            estimated_cost="$1,000 - $3,000/year typical premium",
            priority=2
        ))

        # Sort by priority and deadline
        tasks.sort(key=lambda t: (t.priority, t.deadline))

        return tasks

    def _assess_timeline_status(
        self,
        deadlines: List[Deadline],
        today: date
    ) -> Tuple[str, List[str]]:
        """Assess overall timeline status and generate warnings."""
        warnings = []

        overdue_deadlines = [d for d in deadlines if d.days_remaining < 0 and not d.completed]
        critical_deadlines = [d for d in deadlines if d.urgency == UrgencyLevel.CRITICAL and d.days_remaining >= 0]
        high_urgency_deadlines = [d for d in deadlines if d.urgency == UrgencyLevel.HIGH and d.days_remaining >= 0]

        if overdue_deadlines:
            status = "AT_RISK"
            for d in overdue_deadlines:
                warnings.append(f"OVERDUE: {d.name} was due on {d.date.strftime('%d %B %Y')}")
        elif critical_deadlines:
            status = "URGENT"
            for d in critical_deadlines:
                warnings.append(f"CRITICAL: {d.name} due in {d.days_remaining} day(s) - {d.date.strftime('%d %B')}")
        elif high_urgency_deadlines:
            status = "ATTENTION_NEEDED"
            for d in high_urgency_deadlines:
                warnings.append(f"HIGH PRIORITY: {d.name} due in {d.days_remaining} days")
        else:
            status = "ON_TRACK"

        return status, warnings

    def update_task_status(
        self,
        timeline: TimelineResult,
        task_name: str,
        new_status: TaskStatus,
        notes: Optional[str] = None
    ) -> TimelineResult:
        """Update the status of a delegated task."""
        for task in timeline.delegated_tasks:
            if task.task == task_name:
                task.status = new_status
                if notes:
                    task.notes = notes
                break

        # Recalculate overall status
        today = date.today()
        timeline.overall_status, timeline.warnings = self._assess_timeline_status(
            timeline.critical_deadlines, today
        )

        return timeline

    def mark_deadline_completed(
        self,
        timeline: TimelineResult,
        deadline_name: str
    ) -> TimelineResult:
        """Mark a deadline as completed."""
        for deadline in timeline.critical_deadlines:
            if deadline.name == deadline_name:
                deadline.completed = True
                break

        return timeline


# Convenience function for quick timeline creation
def create_due_diligence_timeline(
    contract_signed: str,
    settlement_date: str,
    cooling_off_expires: Optional[str] = None,
    special_conditions: Optional[List[Dict[str, Any]]] = None,
    property_type: str = "house",
    is_investment: bool = False
) -> Dict[str, Any]:
    """
    Quick timeline creation.

    Args:
        contract_signed: Date string in YYYY-MM-DD format
        settlement_date: Date string in YYYY-MM-DD format
        cooling_off_expires: Optional cooling-off expiry date
        special_conditions: List of special conditions
        property_type: Type of property
        is_investment: Whether investment purchase

    Returns:
        Dict with timeline details
    """
    signed = date.fromisoformat(contract_signed)
    settlement = date.fromisoformat(settlement_date)
    cooling_off = date.fromisoformat(cooling_off_expires) if cooling_off_expires else None

    timeline = DueDiligenceTimeline()
    result = timeline.create_timeline(
        contract_signed_date=signed,
        cooling_off_expires=cooling_off,
        settlement_date=settlement,
        special_conditions=special_conditions or [],
        property_type=property_type,
        is_investment=is_investment
    )

    return result.to_dict()
