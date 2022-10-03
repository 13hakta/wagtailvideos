function createVideoChooser(id) {
    var chooserElement = $('#' + id + '-chooser');
    var previewVideo = chooserElement.find('.preview-image img');
    var input = $('#' + id);
    var editLink = chooserElement.find('.edit-link');

    document.addEventListener('DOMContentLoaded', event => {
        $.ajax(window.chooserUrls.videoChooser + input.val()).done(data => {
            let videoData = data.result
            input.val(videoData.id);
            previewVideo.attr({
                src: videoData.preview.url,
                alt: videoData.title
            });
            chooserElement.removeClass('blank');
            editLink.attr('href', videoData.edit_link);
        });
    });

    $('.action-choose', chooserElement).click(function() {
        ModalWorkflow({
            url: window.chooserUrls.videoChooser,
            onload: VIDEO_CHOOSER_MODAL_ONLOAD_HANDLERS,
            responses: {
                videoChosen: function(videoData) {
                    input.val(videoData.id);
                    previewVideo.attr({
                        src: videoData.preview.url,
                        alt: videoData.title
                    });
                    chooserElement.removeClass('blank');
                    editLink.attr('href', videoData.edit_link);
                }
            }
        });
    });

    $('.action-clear', chooserElement).click(function() {
        input.val('');
        chooserElement.addClass('blank');
    });
}
