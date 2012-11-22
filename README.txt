=====
SRFAX
=====

`SRFAX`_ is a feature rich internet fax service which encompasses all aspects of
fax communications with easy to use online fax management services. Online
faxing services provided by `SRFAX`_ is simple, reliable, inexpensive and can also
be used from mobile devices. Internet faxing is simple and easy as can be
accessed using your email and so it is private and secure.

SRFAX is a registered trademark of EDC Systems, Inc. 


SRFAX API for Python
====================

SRFAX API enables you to:

* Schedule a fax to be sent

* Determine the status of a fax that has been scheduled for delivery

* Retrieve a list of faxes received in a specified period of time

* Retrieve a list of faxes sent in a specified period of time

* Retrieve a specified sent or received fax file in PDF or TIFF format

* Delete specified received or sent faxes.


Example Usage
-------------

.. code-block:: python

    from srfax import srfax

    srfax_client = srfax.SRFax(<SRFAX_ACCESS_ID>,
                               <SRFAX_ACCESS_PWD>,
                               caller_id=<SRFAX_CALLER_ID>,
                               sender_email=<SRFAX_SENDER_EMAIL>)

    fax_id = srfax_client.queue_fax('+11234567', '/path/to/fax/file')
    status = srfax_client.get_fax_status(fax_id)
        

Copyright and License
---------------------

SRFAX API is Copyright (c) 2012 Vingd, Inc. and licensed under the MIT license
(see LICENSE.txt).


.. _`SRFAX`: http://www.srfax.com/
