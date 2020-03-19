def get_changed_fields(new_record, old_record):
    if hasattr(new_record, "get_changed_fields"):
        return new_record.get_changed_fields(old_record)
    return new_record.diff_against(old_record).changed_fields
