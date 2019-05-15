
import uno
import unohelper
from com.sun.star.awt import XContainerWindowEventHandler
# from com.sun.star.awt import XActionListener
# from com.sun.star.lang import XServiceInfo
from com.sun.star.beans import PropertyValue
from com.sun.star.awt.MessageBoxType import ERRORBOX
from com.sun.star.awt.MessageBoxButtons import BUTTONS_OK

import lotranslate_backend


def message_box(message_text):
    ctx = uno.getComponentContext()
    sManager = ctx.ServiceManager
    toolkit = sManager.createInstance("com.sun.star.awt.Toolkit")
    msgbox = toolkit.createMessageBox(None, ERRORBOX, BUTTONS_OK, "Error",
                                      message_text)
    return msgbox.execute()


def configuration_access(path, write=False):
    """Creates a XNameAccess instance for read and write access to the
    configuration at the given node path."""

    ctx = uno.getComponentContext()
    configurationProvider = ctx.ServiceManager.createInstance(
        'com.sun.star.configuration.ConfigurationProvider')
    value = PropertyValue()
    value.Name = 'nodepath'
    value.Value = path
    if write:
        servicename = 'com.sun.star.configuration.ConfigurationUpdateAccess'
    else:
        servicename = 'com.sun.star.configuration.ConfigurationAccess'
    configurationAccess = configurationProvider.createInstanceWithArguments(
        servicename, (value,))
    return configurationAccess


class CfgDialogEventHandler(unohelper.Base, XContainerWindowEventHandler):
    def __init__(self, context):
        # import pydevd; pydevd.settrace()
        self.context = context
        # Names of the controls which are supported by this handler. All these
        # controls must have a "Text" property.
        self.controlNames = {"chkEditBeforeReplace", "lstTranslationModels"}

        self.edit_before_replace = True
        self.models = []
        # self.__serviceName = "org.openoffice.demo.DialogEventHandler"

    def add_model(self, window):
        sman = self.context.getServiceManager()
        filepicker = sman.createInstanceWithContext(
            "com.sun.star.ui.dialogs.FilePicker", self.context)
        if filepicker.execute():
            # d = filepicker.getDisplayDirectory()
            fns = filepicker.getFiles()
            fn = fns[0] if fns else None
        else:
            fn = None
        filepicker.dispose()
        if fn is not None:
            cfg = self.load_model_config(fn)
            if cfg is not None:
                self.models.append(cfg)
                self.update_dialog(window)
            else:
                message_box("Could not load model config")

    def load_model_config(self, url):
        path = unohelper.fileUrlToSystemPath(url)
        cfg = lotranslate_backend.load_model_config(path)
        if cfg is not None:
            cfg['lotranslate-path-url'] = url
        return cfg

    def load_config(self, window):
        cfg_access = configuration_access(
            "/de.lernapparat.lotranslate.Options/Options")
        self.edit_before_replace = cfg_access.getByName('chkEditBeforeReplace')
        model_urls = cfg_access.getByName('lstTranslationModels')
        self.models = []
        for u in model_urls:
            cfg = self.load_model_config(u)
            if cfg is not None:
                self.models.append(cfg)
        self.update_dialog(window)

    def save_config(self, window):
        # import pydevd; pydevd.settrace()
        update_access = configuration_access(
            "/de.lernapparat.lotranslate.Options/Options", write=True)
        update_access.setPropertyValue('chkEditBeforeReplace',
                                       self.edit_before_replace)
        urls = tuple(m['lotranslate-path-url'] for m in self.models)
        # update_access.setPropertyValue('lstTranslationModels', urls)
        # does not work
        # see https://bugs.documentfoundation.org/show_bug.cgi?id=125307
        uno.invoke(update_access, "setPropertyValue",
                   (('lstTranslationModels', uno.Any("[]string", urls))))
        update_access.commitChanges()

    def update_dialog(self, window):
        model_list = window.getControl("lstTranslationModels")
        model_list.removeItems(0, model_list.getItemCount())
        # use Language specific menu entry instead of '*'
        model_list.addItems([m['menu_entry']['*'] for m in self.models], 0)

    def callHandlerMethod(self, window, event, method):
        # method is a string
        # event can be string or an object (e.g. ActionEvent object)
        # window is com.sun.star.awt.XWindow, but really XContainerWindow
        # first: "external_event" event: "initialize"
        # NewModel button: "actionNewModel" (defined in xdl), event: ActionEvent object
        if method == "external_event":
            if event == "initialize" or event == "back":  # initialization or "Reset" button
                self.load_config(window)
                return True
            elif event == "ok":
                self.save_config(window)
                return True
            else:
                import pydevd; pydevd.settrace()  # noqa: E702
                return False
        elif method == "actionNewModel":
            self.add_model(window)
            return True
        elif method == "actionEditModel":
            return True  # edit model button
        elif method == "actionDeleteModel":
            return True  # delete model button
        else:
            import pydevd; pydevd.settrace()  # noqa: E702
            return False
        return False

    def getSupportedMethodNames(self):
        # import pydevd; pydevd.settrace()
        return ["external_event"]  # is this needed? seems to not be called...

    def createUnoService(self, name):
        pass