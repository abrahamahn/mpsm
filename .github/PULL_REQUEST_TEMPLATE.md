# Pull Request

## Description

<!-- Provide a brief description of your changes -->

Fixes #(issue number)

## Type of Change

<!-- Mark relevant options with an 'x' -->

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Performance improvement
- [ ] Test addition/improvement

## Changes Made

<!-- List the main changes made in this PR -->

-
-
-

## Testing

<!-- Describe the tests you ran and how to reproduce them -->

### Test Configuration

- **Python Version**:
- **OS**:
- **MPSM Version**:

### Tests Run

```bash
# Example commands used for testing
pytest tests/
```

### Test Results

- [ ] All existing tests pass
- [ ] New tests added (if applicable)
- [ ] Manual testing performed

## Screenshots (if applicable)

<!-- Add screenshots to help explain your changes -->

## Checklist

<!-- Mark completed items with an 'x' -->

### Code Quality

- [ ] My code follows the project's style guidelines (Black formatting)
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] My changes generate no new warnings
- [ ] I have run `black src/ tests/ mpsm.py` for formatting
- [ ] I have run `mypy src/` for type checking (or addressed known issues)

### Testing

- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] I have run the full test suite with `pytest tests/ -v`
- [ ] Test coverage has been maintained or improved

### Documentation

- [ ] I have updated the documentation accordingly
- [ ] I have updated docstrings for new/modified functions
- [ ] I have added examples for new features (if applicable)
- [ ] I have updated the CHANGELOG.md

### Commits

- [ ] My commits follow the conventional commits format
- [ ] My commits are atomic and have descriptive messages
- [ ] I have rebased my branch on the latest main

### Dependencies

- [ ] I have updated requirements.txt (if dependencies changed)
- [ ] I have updated pyproject.toml (if dependencies changed)
- [ ] New dependencies are justified and documented

## Breaking Changes

<!-- If this PR includes breaking changes, describe them here -->

- [ ] This PR includes no breaking changes

If breaking changes exist:
-
-

## Additional Notes

<!-- Add any additional notes or context for reviewers -->

## Related Issues

<!-- Link related issues using keywords: Fixes #123, Relates to #456, etc. -->

-
-

## Reviewer Notes

<!-- Any specific areas you'd like reviewers to focus on? -->

---

**For Maintainers:**
- [ ] Reviewed code changes
- [ ] Checked test coverage
- [ ] Verified documentation updates
- [ ] Confirmed CI/CD passes
- [ ] Ready to merge
