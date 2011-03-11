(function() {
    YAHOO.bethel.contentlayout.NewsItemTool = function(el, userConfig) {
        YAHOO.bethel.contentlayout.NewsItemTool.superclass.constructor.call(this, el, userConfig);
        this.infopanel = null;
    }
    
    /* NewsItemTool is a ContentLayout InfoPanel module for configuring the
       properties of News and Agenda Items (similar to the old properties toolbox
       in kupu) */

    var Lang = YAHOO.lang,
        Module = YAHOO.widget.Module,
        NewsItemTool = YAHOO.bethel.contentlayout.NewsItemTool,
        EditorPanel = YAHOO.bethel.contentlayout.EditorPanel,
        getData = YAHOO.bethel.contentlayout.getData,
        Dom = YAHOO.util.Dom,
        Event = YAHOO.util.Event,
        Selector = YAHOO.util.Selector,
        Button = YAHOO.widget.Button,
        Panel = YAHOO.widget.Panel,
        SimpleDialog = YAHOO.widget.SimpleDialog,
        Connect = YAHOO.util.Connect;
        
    Lang.extend(NewsItemTool, Module, {
        init: function(el, userConfig) {
            NewsItemTool.superclass.init.call(this, el, userConfig);
            /* create the error dialog that is displayed when the properties
               form was submitted with errors */
            this.errorDialog = new SimpleDialog("news-properties-error-dlg", {
                width: "20em",
                fixedcenter: true,
                modal: true,
                visible: false,
                draggable: false }
            );
            this.errorDialog.setHeader("Error Saving Properties");
            this.errorDialog.cfg.queueProperty("icon",SimpleDialog.ICON_ALARM);
            this.errorDialog.cfg.queueProperty("buttons",
              [ {text: "Continue", handler: function() { this.hide(); } } ]
            );
            this.errorDialog.render(this.element.ownerDocument.getElementById('content-layout'));
        },
        
        panelOpened: function() {
            /* called when the info panel is opened. */
            return;
        },
        
        panelClosed: function() {
            /* called when the info panel is closed. */
            /* we don't need to do anything special when it is closed */
            return;
        },
        
        installIntoPanel: function(panel) {
            /* this is called by the InfoPanel.  This method installs the
               tool into the infopanel.  This is done by issuing an AJAX
               request to zope to retrieve the tool's html, then inserting
               it into this module's body (via the initializeTool method) */
            this.infopanel = panel;
            var toolButtonName = this.element.id + "button"
            this.render();
            this.toolButton = new Button({id: toolButtonName,
                                            type: "button",
                                            title: "News Properties",
                                            container: this.body,
                                            value: "props",
                                            onclick: {fn: function(ev) {
                                                            this.openPropertiesDialog()
                                                        },
                                                      scope: this}
                                            }
                                          );
            this.toolButton.addClass("infopanel-button");
                                          
            /* create the edit news properties dialog */
            this.editDialog = new EditorPanel("news-properties-edit-dlg",{
                width: '600px',
                height: '560px',
		modal: true,
		draggable: false,
                fixedcenter: true,
                close: true,
                visible: false,
                submitLabel: "Save Properties",
                defaultTitle: "Edit News Properties",
                dialogUrl: objurl + "/tab_edit_snn_get_properties_tool",
                submitCallback: {fn: this.saveProperties, scope: this}
            }, this.infopanel.app);
            /*add the dialog directly inside the 'content-layout' container.
              this ensures that it receives the same styling treatment as
              the other dialogues */
	    this.editDialog.render(this.element.ownerDocument.getElementById('content-layout'));
        }, /* end installInfoPanel */
        
        openPropertiesDialog: function() {
            this.editDialog.show();
            
        },
        
        initializeTool: function() {
        /* XXX this isn't called anymore */
            this.indicator = Selector.query('img',this.iframe.document.body, true);
        }, /* end initializeTool */
        
        saveProperties: function() {
            /* this method is called when the "save properties" button is
               clicked.  This method prepares and sends the POST, and either
               refreshes the body on success (via initializeTool) or displays
               the error dialog (on error) */
               
            if_doc = this.editDialog.editorIFrame.document
            /* display indicator gif */
            var indicator = Selector.query('img.indicator', if_doc.body, true);
            Dom.setStyle(indicator,'display','inline');

            var postData = getData(if_doc.body);
            /* the 'save properties' button is not captured via
               getData (YUI doesn't consider it data), but it is
               needed in the POST in order for zope to trigger
               the appropriate action.  if not present, zope
               thinks that the form is being requested. */
            postData['form.buttons.apply'] = 'Apply';
            var post = []
            for (var name in postData) {
                var value = postData[name];
                if (!(value instanceof Array)) {
                    value = [value];
                }
                for (var i=0; i < value.length; i++) {
                    post.push(encodeURIComponent(name) + '=' + encodeURIComponent(value[i]));
                }
            }
            post = post.join("&");
            
            /* post to the properties tool */
            var url = objurl + "/tab_edit_snn_get_properties_tool";
            Connect.asyncRequest('POST', 
                url,
                {success: function(resp) { 
                        Dom.setStyle(indicator, 'display','none');
                        var docEl = this.element.ownerDocument;
                        var frag = docEl.createDocumentFragment();
                        var div = docEl.createElement("div");
                        div.innerHTML = resp.responseText;
                        frag.appendChild(div);
                        var errorDOM = Selector.query('ul.errors',frag.childNodes[0],true);
                        if (errorDOM) {
      			    this.errorDialog.cfg.setProperty("text", errorDOM.innerHTML);
                            this.errorDialog.show();
                        } else {
                            /* success.  close the panel, reload iframe */
                            this.editDialog.hide();
                            this.editDialog.editorIFrame.location.reload();
                        }
                        /* turn off indicator, close dialog */
                 },
                 failure: function(resp, a, b, c) {
                    Dom.setStyle(indicator, 'display','none');
                    alert('failure in saving properties: \n' +resp.responseText)
                 },
                 scope: this,
                 argument: {indicator: indicator}
                },
                post
            );
        } /* end saveProperties */
        
    }); /* end Lang.extend */

    YAHOO.util.Event.onDOMReady(function() {
        var clap =window.ContentLayoutApp;
        if (!clap.infopanel) {
            /* the editor isn't present on this page, so stop loading it.
                this can happen if contentlayout is used for versionedcontent
                and there is no published version. */
            return;
        }
        clap.infopanel.registerTool("newsitemtool", new NewsItemTool("infopanel-newsitemtool"));
    });

}());
