# TODO - Future Improvements

## High Priority

### Local Development Scripts
- **run_server.sh**: Currently excluded from git (contains machine-specific paths)
  - Create a portable version that works across different environments
  - Consider using environment variables or relative paths
  - Alternative: Create a proper setup script that generates machine-specific files
  - Status: Local quick fix, needs proper implementation

## Completed ✅

### Analytics Implementation
- ✅ **Analytics Module**: Complete analytics tracking system implemented (2025-06-27)
  - Usage tracking for all MCP tools with decorators
  - Performance metrics (response times, cache efficiency)
  - Error tracking and rate limiting monitoring
  - Persistent storage with periodic flushing
  - MCP tools for analytics: `get_analytics_summary`, `get_detailed_metrics`, `reset_analytics`
  - Comprehensive test suite with successful validation

## Medium Priority

### Configuration
- Review and update author information in pyproject.toml if needed
- Consider adding more comprehensive development documentation
- Add contribution guidelines

## Low Priority

### Documentation
- Add more examples for different research fields
- Create troubleshooting guide
- Add performance optimization tips

---

**Notes:**
- This file tracks improvements needed for the project
- Items can be moved between priority levels as needed
- Mark completed items with ✅ and date
