from rest_framework import serializers


class DocumentsField(serializers.ListField):
    def to_representation(self, value):
        return [
            {
                "id": document.id,
                "name": document.original_filename,
                "size": document.size,
                "status": document.document.status,
            }
            for document in value.all()
        ]

    def custom_update(self, validated_data):
        instance = self.parent.instance
        documents = validated_data.get("documents", [])
        instance.documents.set(documents)
