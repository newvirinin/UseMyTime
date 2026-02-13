# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitLab CI/CD pipeline configuration
- Comprehensive documentation
- Environment configuration template
- Contributing guidelines

### Changed
- Updated README with detailed installation instructions
- Improved project structure documentation

## [1.0.0] - 2024-02-13

### Added
- Complete time tracking system with automatic timer stop
- Role-based access control (Employee, Manager, Director)
- Project management with tasks and status tracking
- Project review workflow with attachments
- PDF report generation for employees, teams, and company
- Responsive Bootstrap UI with dynamic forms
- Comprehensive test coverage (100% pass rate)
- UML use case diagrams for all user roles
- Academic documentation for thesis work

### Fixed
- Missing `project_review_count` function causing server startup error
- Timer reliability issues with page close using `navigator.sendBeacon`
- Role-based permissions and validation
- File attachment system implementation
- Comprehensive error handling throughout the application

### Security
- CSRF protection implementation
- XSS prevention measures
- SQL injection protection through Django ORM
- Secure file upload handling
- Role-based access control

### Performance
- Optimized database queries with select_related and prefetch_related
- Efficient timer management
- Static file optimization
- Database indexing for frequently accessed fields

### Documentation
- Complete UML diagrams for all user roles
- Database schema documentation
- API documentation
- Installation and deployment guides

### Testing
- Unit tests for all models and views
- Integration tests for workflows
- Frontend JavaScript tests
- Performance tests
- Security tests

### Infrastructure
- Docker support (planned)
- CI/CD pipeline with GitLab
- Automated testing and deployment
- Code quality checks

## [0.9.0] - 2024-01-30

### Added
- Basic user authentication system
- Simple project creation and management
- Basic time tracking functionality
- Initial database schema

### Known Issues
- Timer stops incorrectly on page close
- Missing role-based permissions
- Limited reporting capabilities
- Basic UI without responsive design

## [0.8.0] - 2024-01-15

### Added
- Initial Django project setup
- Basic user models
- Simple project models
- Basic templates

### Known Issues
- No time tracking functionality
- No role management
- No reporting system
- Minimal testing coverage
