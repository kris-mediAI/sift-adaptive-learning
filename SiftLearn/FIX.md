# Sift Backend Compatibility Fixes v2

IMPORTANT: v1 had an incorrect session fix. It removed `self` but left
`@staticmethod`, which caused `NameError: name 'self' is not defined`.

v2 correctly makes `_validate_assessment` an instance method:

    def _validate_assessment(self, assessment):

This is required because it accesses `self.engine.knowledge_graph`.

The LearningRecord and ContentEngine compatibility fixes are unchanged.
