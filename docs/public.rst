.. toctree::
   :maxdepth: 4

API Objects
###########
The classes and functions documented on this page constitute the public API to
the okcupyd library.

:class:`~okcupyd.user.User`
===========================

:class:`~okcupyd.user.User` serves as the primary entry point to the okcupyd
library. Most of the objects mentioned on this page are accessible in some way
or another from instances of :class:`~okcupyd.user.User`.

.. autoclass:: okcupyd.user.User
    :members:
    :special-members: __init__

:class:`~okcupyd.profile.Profile`
=================================

.. autoclass:: okcupyd.profile.Profile
    :members:
    
:class:`~okcupyd.looking_for.LookingFor`
========================================
.. autoclass:: okcupyd.looking_for.LookingFor
    :members:
    
:class:`~okcupyd.details.Details`
=================================
.. autoclass:: okcupyd.details.Details
    :members:
    
:class:`~okcupyd.essay.Essays`
==============================
.. autoclass:: okcupyd.essay.Essays
    :members:

:class:`~okcupyd.photo.PhotoUploader`
=====================================

.. autoclass:: okcupyd.photo.PhotoUploader
    :members:
    
:class:`~okcupyd.photo.Info`
============================
.. autoclass:: okcupyd.photo.Info
    :members:
    
:class:`~okcupyd.messaging.MessageThread`
=========================================
.. autoclass:: okcupyd.messaging.MessageThread
    :members:
    
:class:`~okcupyd.messaging.Message`
===================================
.. autoclass:: okcupyd.messaging.Message
    :members:
    
:class:`~okcupyd.question.Questions`
====================================
.. autoclass:: okcupyd.question.Questions
    :members:
    
:class:`~okcupyd.question.Question`
===================================
.. autoclass:: okcupyd.question.Question
    :members:
    
:class:`~okcupyd.question.UserQuestion`
=======================================

.. autoclass:: okcupyd.question.UserQuestion
    :members:

:class:`~okcupyd.question.AnswerOption`
=======================================

.. autoclass:: okcupyd.question.AnswerOption
    :members:
    
:func:`~okcupyd.search.SearchFetchable`
========================================
.. autofunction:: okcupyd.search.SearchFetchable
    
:class:`~okcupyd.attractiveness_finder.AttractivenessFinder`
============================================================
.. autoclass:: okcupyd.attractiveness_finder.AttractivenessFinder
    :members:
    
:class:`~okcupyd.statistics.Statistics`
=======================================
.. autoclass:: okcupyd.statistics
    :members:

:func:`~okcupyd.util.misc.add_command_line_options`
===================================================
.. autofunction:: okcupyd.util.misc.add_command_line_options

:func:`~okcupyd.util.misc.handle_command_line_options`
======================================================
.. autofunction:: okcupyd.util.misc.handle_command_line_options
