PloneQuickUpload.addUploadFields = function(uploader, domelement, file, id, fillTitles, fillDescriptions) {
    var blocFile;
    if (fillTitles || fillDescriptions)  {
        blocFile = uploader._getItemByFileId(id);
        if (typeof id == 'string') id = parseInt(id.replace('qq-upload-handler-iframe',''));
    }
    var typeupload = $('input.uploadify_typeupload').val();
    jQuery('.qq-upload-cancel', blocFile).after('<div class="content"></div>');
    jQuery(blocFile).find('div.content').load(
      '@@quickupload-form',
      {'typeupload': typeupload},
      function(){
        var select = $(this).find('select#form-widgets-content_category');
        if (select.length) {
            select.width('100%');
            IconifiedCategory.initializeCategoryWidget(select);
            // pat-select2 (plone.app.z3cform): patterns are not scanned in content loaded by jQuery
            select.on('init.select2.patterns', function() {
                IconifiedCategory.showCategoryIcons(select);
            });
            new window.__patternslib_registry['select2'](select);
        }
      }
    );

    PloneQuickUpload.showButtons(uploader, domelement);
};


PloneQuickUpload.sendDataAndUpload = function(uploader, domelement, typeupload) {
    var handler = uploader._handler;
    var files = handler._files;
    var missing = 0;
    // CSRF token (plone.protect aborts the upload without it)
    var authenticator = jQuery(domelement).closest('.quick-uploader').find('input[name="_authenticator"]').val();
    for ( var id = 0; id < files.length; id++ ) {
        if (files[id]) {
            var fileContainer = jQuery('.qq-upload-list li', domelement)[id-missing];
            var title = jQuery('input[name="form.widgets.title"]', fileContainer).val();
            var description = jQuery('textarea[name="form.widgets.description"]', fileContainer).val();
            var category = '';
            category_element = jQuery('select[name="form.widgets.content_category"]', fileContainer);
            if (category_element.length) {
                category = category_element.val();
            }
            uploader._queueUpload(id, {'title': title, 'description': description, 'content_category': category, 'typeupload': typeupload, '_authenticator': authenticator});

        }
        // if file is null for any reason jq block is no more here
        else missing++;
    }
};

PloneQuickUpload.extendCategories = function() {
  var first_element = $('select#form-widgets-content_category:first');
  var category = first_element.val();

  $('select#form-widgets-content_category').each(function() {
    $(this).val(category);
    $(this).trigger('change');
  });
  return false;
};
