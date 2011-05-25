(function ($) {

    $('.tree-widget-jstree .jstree-checkbox').live('click', function(){
        var checkbox = $(this);
        var li = checkbox.closest('li');
        var value = li.attr('id');
        var checked = li.hasClass('jstree-checked');
        var tree = $(this).closest('.tree-widget-jstree');
        var input = tree.siblings('input.tree-input');
        var values = [];
        $.each(tree.jstree('get_checked'), function(index, node){
            values.push(node.id);
        });
        input.val(values.join('|'));
    });

    function loadTrees(event) {
        var tree = $(".tree-widget-jstree");
        console.log(tree)

        tree.jstree({
            "plugins" : ["html_data", "checkbox"]
        });
    };

    $(document).bind('zeam-form-ready', loadTrees);

})(jQuery);
