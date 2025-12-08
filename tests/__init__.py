"""
Test package.
🎓 TESTING STRUCTURE:

tests/
├── __init__.py
├── conftest.py          # Shared fixtures
├── unit/                # Unit tests
│   ├── __init__.py
│   ├── test_services/
│   │   ├── test_user_service.py
│   │   ├── test_project_service.py
│   │   └── test_task_service.py
│   └── test_repositories/
│       └── test_user_repository.py
├── integration/         # API integration tests
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_projects.py
│   └── test_tasks.py
└── factories/           # Test data factories
    ├── __init__.py
    └── user_factory.py
"""