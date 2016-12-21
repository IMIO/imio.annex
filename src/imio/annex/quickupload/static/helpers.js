PloneQuickUpload.addUploadFields = function(uploader, domelement, file, id, fillTitles, fillDescriptions) {
    var blocFile;
    if (fillTitles || fillDescriptions)  {
        blocFile = uploader._getItemByFileId(id);
        if (typeof id == 'string') id = parseInt(id.replace('qq-upload-handler-iframe',''));
    }
    var container = $(blocFile).closest('.uploaderContainer');
    var typeupload = container.find('input.uploadify_typeupload').val();
    jQuery('.qq-upload-cancel', blocFile).after('<div class="content"></div>');
    jQuery(blocFile).find('div.content').load(
      '@@quickupload-form',
      {'typeupload': typeupload},
      function(){
        var select = $(this).find('select#form_widgets_content_category');
        select.width('100%');
        IconifiedCategory.initializeCategoryWidget(select);
        initializeSelect2SingleWidget(select);
      }
    );

    PloneQuickUpload.showButtons(uploader, domelement);
};


PloneQuickUpload.sendDataAndUpload = function(uploader, domelement, typeupload) {
    var handler = uploader._handler;
    var files = handler._files;
    var missing = 0;
    for ( var id = 0; id < files.length; id++ ) {
        if (files[id]) {
            var fileContainer = jQuery('.qq-upload-list li', domelement)[id-missing];
            var title = jQuery('input[name="form.widgets.title"]', fileContainer).val();
            var description = jQuery('textarea[name="form.widgets.description"]', fileContainer).val();
            var category = jQuery('select[name="form.widgets.content_category:list"]', fileContainer).val();
            uploader._queueUpload(id, {'title': title, 'description': description, 'content_category': category, 'typeupload': typeupload});

        }
        // if file is null for any reason jq block is no more here
        else missing++;
    }
};

PloneQuickUpload.extendCategories = function() {
  var container = $(this).closest('div.uploaderContainer');
  var first_element = container.find('select#form_widgets_content_category:first');
  var category = first_element.val();

  container.find('select#form_widgets_content_category').each(function() {
    $(this).val(category);
    $(this).trigger('change');
  });
  return false;
};
