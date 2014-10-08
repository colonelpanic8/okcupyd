.. toctree::
   :maxdepth: 4

Public Interface Objects
########################
The objects on this page are the ones that developers who are using okcupyd
should expect to interact with during normal use of the library.
Though you are welcome to do so, it is not necessary to familiarize yourself
with any of the other objects mentioned in these docs or found elsewhere in
the codebase.

:class:`~okcupyd.user.User`
===========================

:class:`~okcupyd.user.User` serves as the primary entry point to the okcupyd
library. All of the objects mentioned on this page are accessible in some way
or another from an instances of :class:`~okcupyd.user.User`.

.. autoclass:: okcupyd.user.User
    :members:
    :special-members: __init__

:class:`~okcupyd.profile.Profile`
=================================
Though it has quite a bit of functionality itself, the
:class:`~okcupyd.profile.Profile` class delegates much of its most of
its responsibilities to its many child objects:
:class:`~okcupyd.looking_for.LookingFor`, :class:`~okcupyd.details.Details`,
:class:`~okcupyd.essay.Essays`, :class:`~okcupyd.photo.Info`

each of these objects has a relatively narrow, self contained resposibility.
Profile objects that belong to a profile that has a session that belongs to
the same user as the profile can be used to update the users profile.

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
========================================
.. autofunction:: okcupyd.util.misc.add_command_line_options

:func:`~okcupyd.util.misc.handle_command_line_options`
========================================
.. autofunction:: okcupyd.util.misc.handle_command_line_options
