class Role:
    ADMIN = "Admin"
    USER = "User"
    VIEWER = "Viewer"

    ALL = [ADMIN, USER, VIEWER]

    CHOICES = [
        (ADMIN, "Admin"),
        (USER, "User"),
        (VIEWER, "Viewer"),
    ]
