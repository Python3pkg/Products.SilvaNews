$Revision: 1.12.4.1 $

Copyright (c) 2002, 2004 Infrae. All rights reserved.
See also LICENSE.txt

Meta::

  Valid for:   Silva News 0.9
  Authors:     Guido Wesdorp, Martijn Faassen, Guido Goldstein
  Emails:      guido@infrae.com, faassen@infrae.com, gst@infrae.com
  CVS:         $Revision: 1.12.4.1 $

Silva News

  Silva is a Zope-based web application designed for the creation and
  management of structured, textual content. Silva allows users to
  enter new documents as well as edit existing documents using a web
  interface.

  Silva News is an extension to Silva to allow authors to place news-
  and agendaitems on the Silva site and show them on a page. Silva
  News is a Silva add-on which can be used on Silva versions 0.9.3 and
  up.

  There are versions for older Silva versions available for download
  as well. No other products are required to use Silva News from
  Silva, besides the products required to run Silva itself.

Installing Silva News

  See INSTALL.txt

Using Silva News

  The first thing to do is add subjects and target audiences to the
  service_news object in the Silva root in the ZMI. This object is
  used only to manage those lists (subjects and target audiences),
  these will function as criteria for the newsfilters (more on these
  later in this document) to search on. It would be best to add as
  much subjects and target audiences as currently available to the
  service when setting up News, since the lists are the basis of the
  filtering system and one has to dive into the ZMI to add items
  (therefore it requires appropriate rights to edit stuff in the ZMI). 
  Managing these lists is quite straightforward: you can add an item
  by filling in a string into one of the textfields and pressing on
  the corresponding 'add' button, and remove them by checking the
  checkbox in front of an item and clicking the corresponding 'remove'
  button.

  Adding a News Publication

    Newsitems can only be added to newsfolders. To add one, go to the
    SMI and choose 'Silva News Publication' from the menu of addables
    (upper right corner of the edit tab in folders, publications and
    the Silva root). Enter an id and a title and choose 'Add and
    edit', you will then be taken to the edit tab of the newsfolder. 
    This tab looks a lot like the edit tab of other containers
    (folders, publications) in Silva, except it doesn't have a default
    document or view and can not contain anything other then newsitems
    and newsfolders (adding newsfolders to other newsfolders allows
    for a more structured setup of the newsfolder).You can add
    newsitems by choosing a specific type from the addables menu in
    this tab.

  Metadata tab

    On the metadata tab of newsfolders there is a checkbox called
    'restrict access'. When this is checked, the folder can only be
    found by news- and agendafilters in the same folder the folder is
    on and each subfolder of that folder. This can be used to make the
    newsfolder 'private', making it available only to for example 1
    department.

  Adding news items

    Now authors can add newsitems. As stated before, there are two
    types of newsitems: plain newsitems and agendaitems. The main
    differences are that agendaitems must contain a date/time on which
    the event described in them takes place, and contain a location on
    which the event takes place. The start date/time is necessary to
    show the items in agendaviewers, since they show the items for a
    particular period (e.g. a month). Therefore agendaviewers can show
    only agendaitems. Newsviewers are capable of showing both news-
    and agendaitems. Other datafields required for the system to work
    correctly are 'subjects' and 'target audiences', which the author
    can use to classify the newsitem. These fields will later be used
    by the newsfilters as criteria for routing the items to
    newsviewers. When editing a news or agenda item, keep in mind that
    the first heading placed in the content editor is considered to be
    the subheader of the newsitem, and the first paragraph as the lead
    (both will show up in the previes on the viewers).

  Adding news filters

    The next thing to do to make the system work is adding one or more
    news- and agendafilters. These are objects used by editors or
    chief- editors to filter a stream of newsitems. The items can be
    filtered on subject and target audience (so for instance a
    newsfilter can route only newsitems with a specific subject or
    meant for a specific target audience to the viewers) and/or as
    individual newsitems.

  The Publication's tab

    The edit tab of a newsfilter (called 'Sources' instead of 'Edit')
    shows a list of all available newsfolders (excluding the one made
    private by checking the 'restrict access' checkbox that are not in
    the same folder or a parentfolder of the newsfilter). To route
    newsitems of a newsfolder to newsviewers (more about those later)
    make sure the checkbox in front of the newsfolder is checked and
    click the 'update folders' button. All (published) newsitems that
    conform to the criteria of the newsfilter will then be routed to
    the newsviewers that use this filter. These criteria can be set in
    the 'Metadata' tab of the newsfilter: you see the lists of
    subjects and target audiences of service_news again, and in
    newsfilters also a couple of radiobuttons to select whether the
    filter should route agendaitems as well as newsitems. These
    criteria can be used to distribute news- and agendaitems in
    different ways across the Silva instance to newsviewers.

    For example: a number of different newsfolders can now contain
    both news- and agendaitems of different subjects and targeting
    different audiences, and the newsfilters filter and distribute
    specific items to viewers. Please note that this means that
    filters must be sensibly set up for the site to allow all
    newsitems to be shown somewhere: it is very easy to set up the
    system in a way that news- and agendaitems with a specific subject
    or target audience are filtered out by all newsfilters, and
    therefore be excluded from all viewers.

  The Items tab

    The 'Items' tab can be used to filter out specific items, to allow
    editors and chiefeditors to disallow specific news- and
    agendaitems to be routed by a filter. To filter out a specific
    item, uncheck the checkbox in front of it and choose 'update'.

  Now the news- and agendaviewers can be placed. The viewers are the
  objects responsible for showing the news- and agendaitems to the
  public. An author can place viewers where he wants news to be shown. 
  The viewers show a list of items routed by the filters.

  The Viewer's Edit tab

    The viewers are quite easy to set up: the only tab that matters is
    the first one (edit), where you can set the number of days the
    viewer will look back (for newsviewers) or ahead (for
    agendaviewers) to get items. In the case of newsviewers there is
    also a switch to choose a number of items to be shown. Also there
    is a list of available filters. All filters chosen here are used
    for retrieving news. When placed, the viewers will be available to
    the public and show news- and/or agendaitems, together with an
    archive (that allows showing items for a particular month) and a
    search option.

    Appending /rss to the URL of a NewsViewer will show the RSS 1.0
    (RDF compliant) view of the items in this viewer.

  The RSSAggregator

    The RSSAggregator replaces the old (and now removed) RSSViewer. In
    the tab_edit you'll see a textbox called 'RSS feeds' where you can
    enter the complete URLs for the feeds you want to have merged by
    this aggregator instance.

    All the other functionality is the same as for News Viewers.

License

  Silva News is released under the BSD license. See 'LICENSE.txt'.
