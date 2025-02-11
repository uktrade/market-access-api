ACTION_PLAN_HISTORY = {
    'name': 'ActionPlanHistory',
    "columns": [
        {'name': 'history_date', 'type': 'timestamp'},
        {'name': 'id', 'nullable': False, 'type': 'varchar'},
        {'name': 'barrier', 'nullable': False, 'type': 'varchar'},
        {'name': 'owner', 'type': 'varchar'},
        {'name': 'current_status', 'nullable': False, 'type': 'varchar'},
        {'name': 'current_status_last_updated', 'type': 'timestamp'},
        {'name': 'status', 'type': 'varchar'},
        {'name': 'strategic_context', 'nullable': False, 'type': 'varchar'},
        {'name': 'strategic_context_last_updated', 'type': 'timestamp'},
        {'name': 'has_risks', 'type': 'varchar'},
        {'name': 'potential_unwanted_outcomes', 'type': 'varchar'},
        {'name': 'potential_risks', 'type': 'varchar'},
        {'name': 'risk_level', 'type': 'varchar'},
        {'name': 'risk_mitigation_measures', 'type': 'varchar'}
    ]
}

BARRIER_HISTORY = {
    'name': 'BarrierHistory',
    'columns': [
        {'name': 'history_date', 'type': 'timestamp'},
        {'name': 'created_on', 'type': 'timestamp'},
        {'name': 'modified_on', 'type': 'timestamp'},
        {'name': 'created_by', 'type': 'varchar'},
        {'name': 'modified_by', 'type': 'varchar'},
        {'name': 'archived', 'nullable': False, 'type': 'boolean'},
        {'name': 'archived_on', 'type': 'timestamp'},
        {'name': 'archived_by', 'type': 'varchar'},
        {'name': 'unarchived_reason', 'nullable': False, 'type': 'varchar'},
        {'name': 'unarchived_on', 'type': 'timestamp'},
        {'name': 'unarchived_by', 'type': 'varchar'},
        {'name': 'id', 'nullable': False, 'type': 'varchar'},
        {'name': 'code', 'type': 'varchar'},
        {'name': 'activity_reminder_sent', 'type': 'timestamp'},
        {'name': 'term', 'type': 'int'},
        {'name': 'estimated_resolution_date', 'type': 'timestamp'},
        {'name': 'proposed_estimated_resolution_date', 'type': 'timestamp'},
        {'name': 'proposed_estimated_resolution_date_created', 'type': 'timestamp'},
        {'name': 'proposed_estimated_resolution_date_user', 'type': 'varchar'},
        {'name': 'estimated_resolution_date_change_reason', 'type': 'varchar'},
        {'name': 'country', 'type': 'varchar'},
        {'name': 'caused_by_admin_areas', 'type': 'boolean'},
        {'name': 'admin_areas', 'nullable': False, 'type': 'array'},
        {'name': 'trading_bloc', 'nullable': False, 'type': 'varchar'},
        {'name': 'caused_by_trading_bloc', 'type': 'boolean'},
        {'name': 'trade_direction', 'type': 'int'},
        {'name': 'sectors_affected', 'type': 'boolean'},
        {'name': 'all_sectors', 'type': 'boolean'},
        {'name': 'sectors', 'nullable': False, 'type': 'array'},
        {'name': 'main_sector', 'type': 'varchar'},
        {'name': 'companies', 'type': 'json'},
        {'name': 'related_organisations', 'type': 'json'},
        {'name': 'product', 'nullable': False, 'type': 'varchar'},
        {'name': 'source', 'nullable': False, 'type': 'varchar'},
        {'name': 'other_source', 'nullable': False, 'type': 'varchar'},
        {'name': 'title', 'nullable': False, 'type': 'varchar'},
        {'name': 'summary', 'nullable': False, 'type': 'varchar'},
        {'name': 'is_summary_sensitive', 'type': 'boolean'},
        {'name': 'next_steps_summary', 'nullable': False, 'type': 'varchar'},
        {'name': 'reported_on', 'nullable': False, 'type': 'timestamp'},
        {'name': 'status', 'nullable': False, 'type': 'int'},
        {'name': 'sub_status', 'nullable': False, 'type': 'varchar'},
        {'name': 'sub_status_other', 'nullable': False, 'type': 'varchar'},
        {'name': 'status_summary', 'nullable': False, 'type': 'varchar'},
        {'name': 'status_date', 'type': 'timestamp'},
        {'name': 'commercial_value', 'type': 'bigint'},
        {'name': 'commercial_value_explanation', 'nullable': False, 'type': 'varchar'},
        {'name': 'economic_assessment_eligibility', 'type': 'boolean'},
        {'name': 'economic_assessment_eligibility_summary', 'nullable': False, 'type': 'varchar'},
        {'name': 'public_eligibility', 'type': 'boolean'},
        {'name': 'public_eligibility_postponed', 'nullable': False, 'type': 'boolean'},
        {'name': 'public_eligibility_summary', 'nullable': False, 'type': 'varchar'},
        {'name': 'top_priority_status', 'nullable': False, 'type': 'varchar'},
        {'name': 'top_priority_rejection_summary', 'type': 'varchar'},
        {'name': 'priority_summary', 'nullable': False, 'type': 'varchar'},
        {'name': 'priority', 'nullable': False, 'type': 'varchar'},
        {'name': 'priority_level', 'nullable': False, 'type': 'varchar'},
        {'name': 'priority_date', 'type': 'timestamp'},
        {'name': 'new_report_session_data', 'nullable': False, 'type': 'varchar'},
        {'name': 'archived_reason', 'nullable': False, 'type': 'varchar'},
        {'name': 'archived_explanation', 'nullable': False, 'type': 'varchar'},
        {'name': 'trade_category', 'nullable': False, 'type': 'varchar'},
        {'name': 'draft', 'nullable': False, 'type': 'boolean'},
        {'name': 'completion_percent', 'type': 'int'},
        {'name': 'start_date', 'type': 'timestamp'},
        {'name': 'is_start_date_known', 'nullable': False, 'type': 'boolean'},
        {'name': 'export_description', 'type': 'varchar'},
        {'name': 'is_currently_active', 'type': 'boolean'}
    ],
}

ECONOMIC_ASSESSMENT_HISTORY = {
    'name': 'EconomicAssessmentHistory',
    'columns': [
        {'name': 'history_date', 'type': 'timestamp'},
        {'name': 'id', 'nullable': False, 'type': 'varchar'},
        {'name': 'created_on', 'type': 'timestamp'},
        {'name': 'modified_on', 'type': 'timestamp'},
        {'name': 'created_by', 'type': 'varchar'},
        {'name': 'modified_by', 'type': 'varchar'},
        {'name': 'archived', 'nullable': False, 'type': 'boolean'},
        {'name': 'archived_on', 'type': 'timestamp'},
        {'name': 'archived_reason', 'nullable': False, 'type': 'varchar'},
        {'name': 'archived_by', 'type': 'varchar'},
        {'name': 'approved', 'type': 'boolean'},
        {'name': 'reviewed_on', 'type': 'timestamp'},
        {'name': 'reviewed_by', 'type': 'varchar'},
        {'name': 'barrier', 'nullable': False, 'type': 'varchar'},
        {'name': 'automated_analysis_data', 'type': 'json'},
        {'name': 'rating', 'nullable': False, 'type': 'varchar'},
        {'name': 'explanation', 'nullable': False, 'type': 'varchar'},
        {'name': 'ready_for_approval', 'nullable': False, 'type': 'boolean'},
        {'name': 'import_market_size', 'type': 'bigint'},
        {'name': 'export_value', 'type': 'bigint'},
        {'name': 'value_to_economy', 'type': 'bigint'}
    ],
}


NEXT_STEP_HISTORY = {
    'name': 'BarrierNextStepItemHistory',
    'columns': [
        {'name': 'history_date', 'type': 'timestamp'},
        {'name': 'created_on', 'type': 'timestamp'},
        {'name': 'modified_on', 'type': 'timestamp'},
        {'name': 'created_by', 'type': 'varchar'},
        {'name': 'modified_by', 'type': 'varchar'},
        {'name': 'id', 'nullable': False, 'type': 'varchar'},
        {'name': 'status', 'nullable': False, 'type': 'varchar'},
        {'name': 'next_step_owner', 'nullable': False, 'type': 'varchar'},
        {'name': 'next_step_item', 'nullable': False, 'type': 'varchar'},
        {'name': 'start_date', 'type': 'timestamp'},
        {'name': 'completion_date', 'type': 'timestamp'},
        {'name': 'barrier', 'nullable': False, 'type': 'varchar'}
    ],
}


TOP_PRIORITY_SUMMARY_HISTORY = {
    'name': 'BarrierTopPrioritySummaryHistory',
    'columns': [
        {'name': 'history_date', 'type': 'timestamp'},
        {'name': 'top_priority_summary_text', 'nullable': False, 'type': 'varchar'},
        {'name': 'created_by', 'type': 'varchar'},
        {'name': 'created_on', 'type': 'timestamp'},
        {'name': 'modified_by', 'type': 'varchar'},
        {'name': 'modified_on', 'type': 'timestamp'},
        {'name': 'barrier', 'nullable': False, 'type': 'varchar'}
    ],
}


PROGRAMME_FUND_PROGRESS_UPDATE_HISTORY = {
    'name': 'ProgrammeFundProgressUpdateHistory',
    'columns': [
        {'name': 'history_date', 'type': 'timestamp'},
        {'name': 'created_by', 'type': 'varchar'},
        {'name': 'modified_by', 'type': 'varchar'},
        {'name': 'archived', 'nullable': False, 'type': 'boolean'},
        {'name': 'archived_on', 'type': 'timestamp'},
        {'name': 'archived_reason', 'nullable': False, 'type': 'varchar'},
        {'name': 'archived_by', 'type': 'varchar'},
        {'name': 'unarchived_reason', 'nullable': False, 'type': 'varchar'},
        {'name': 'unarchived_on', 'type': 'timestamp'},
        {'name': 'unarchived_by', 'type': 'varchar'},
        {'name': 'id', 'nullable': False, 'type': 'varchar'},
        {'name': 'created_on', 'type': 'timestamp'},
        {'name': 'modified_on', 'type': 'timestamp'},
        {'name': 'barrier', 'nullable': False, 'type': 'varchar'},
        {'name': 'milestones_and_deliverables', 'type': 'varchar'},
        {'name': 'expenditure', 'type': 'varchar'}
    ],
}


# Loaded into Dataflow
DATASET_SCHEMAS = {
    "tables": [
        BARRIER_HISTORY,
        ECONOMIC_ASSESSMENT_HISTORY,
        PROGRAMME_FUND_PROGRESS_UPDATE_HISTORY,
        TOP_PRIORITY_SUMMARY_HISTORY,
        NEXT_STEP_HISTORY,
        ACTION_PLAN_HISTORY
    ]
}