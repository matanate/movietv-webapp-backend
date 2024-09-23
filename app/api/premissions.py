from rest_framework.permissions import BasePermission


class IsCurrentUser(BasePermission):
    """
    Custom permission class to check if the current user is the author of the object.
    Inherits from `BasePermission` class.
    Methods:
        - has_object_permission(request, view, obj): Checks if the current user is the author of the object.
    Attributes:
        None
    """

    def has_object_permission(self, request, view, obj):
        # Assumes that the model instance has an `author` attribute.
        if hasattr(obj, "author"):
            return obj.author == request.user
        # check if object type user
        return obj == request.user
