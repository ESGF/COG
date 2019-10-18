function ProtectPath(path) {
    path = path.replace( /\\/g,'\\\\');
    path = path.replace( /'/g,'\\\'');
    return path ;
}

function gup( name ) {
  name = name.replace(/[\[]/,"\\\[").replace(/[\]]/,"\\\]");
  var regexS = "[\\?&]"+name+"=([^&#]*)";
  var regex = new RegExp(regexS);
  var results = regex.exec(window.location.href);
  if(results == null)
    return "";
  else
    return results[1];
}

function OpenFile(fileUrl) {
    var CKEditorFuncNum = gup('CKEditorFuncNum');
    // HACK: FIXME
    if (CKEditorFuncNum==null || CKEditorFuncNum=='') CKEditorFuncNum=2;
    window.top.opener.CKEDITOR.tools.callFunction(CKEditorFuncNum,encodeURI(fileUrl).replace('#','%23'));
    window.top.close();
    window.top.opener.focus();
}
