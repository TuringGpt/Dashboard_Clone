from .add_whiteboard import AddWhiteboard
from .create_doc import CreateDoc
from .create_label_entry import CreateLabelEntry
from .create_list import CreateList
from .delegate_to_human import DelegateToHuman
from .delete_doc import DeleteDoc
from .delete_label_entry import DeleteLabelEntry
from .delete_links_field import DeleteLinksField
from .edit_viewer_permission_on_doc import EditViewerPermissionOnDoc
from .fetch_list import FetchList
from .fetch_whiteboard import FetchWhiteboard
from .find_user_record import FindUserRecord
from .get_doc import GetDoc
from .get_label import GetLabel
from .get_space_info import GetSpaceInfo
from .get_user_permissions import GetUserPermissions
from .grant_admin_on_doc import GrantAdminOnDoc
from .grant_editor_on_doc import GrantEditorOnDoc
from .grant_viewer_on_doc import GrantViewerOnDoc
from .modify_editor_permission_on_doc import ModifyEditorPermissionOnDoc
from .modify_whiteboard import ModifyWhiteboard
from .remove_list import RemoveList
from .remove_whiteboard import RemoveWhiteboard
from .reset_inheritance_on_doc import ResetInheritanceOnDoc
from .set_links_field import SetLinksField
from .update_admin_permission_on_doc import UpdateAdminPermissionOnDoc
from .update_doc import UpdateDoc
from .update_label_entry import UpdateLabelEntry
from .update_links_field import UpdateLinksField
from .update_list import UpdateList

ALL_TOOLS_INTERFACE_4 = [
    AddWhiteboard,
    CreateDoc,
    CreateLabelEntry,
    CreateList,
    DelegateToHuman,
    DeleteDoc,
    DeleteLabelEntry,
    DeleteLinksField,
    EditViewerPermissionOnDoc,
    FetchList,
    FetchWhiteboard,
    FindUserRecord,
    GetDoc,
    GetLabel,
    GetSpaceInfo,
    GetUserPermissions,
    GrantAdminOnDoc,
    GrantEditorOnDoc,
    GrantViewerOnDoc,
    ModifyEditorPermissionOnDoc,
    ModifyWhiteboard,
    RemoveList,
    RemoveWhiteboard,
    ResetInheritanceOnDoc,
    SetLinksField,
    UpdateAdminPermissionOnDoc,
    UpdateDoc,
    UpdateLabelEntry,
    UpdateLinksField,
    UpdateList
]
