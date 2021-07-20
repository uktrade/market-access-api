class DatabaseRouter:
    def db_for_read(self, model, **hints):
        return model._meta.app_label

    def db_for_write(self, model, **hints):
        if model._meta.app_label != "default":
            raise NotImplementedError(f"{model._meta.app_label} database is read only")

        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label != "default" or obj2._meta.app_label != "default":
            return None
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label != "default":
            return None
        return True
