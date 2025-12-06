from .alter_datatype import AlterDatatype
from .alter_document import AlterDocument
from .alter_embed_block import AlterEmbedBlock
from .alter_file import AlterFile
from .alter_tags import AlterTags
from .alter_whiteboard_view import AlterWhiteboardView
from .attain_document_parent_hierarchy import AttainDocumentParentHierarchy
from .collect_document_versions import CollectDocumentVersions
from .create_embed_block import CreateEmbedBlock
from .delete_document import DeleteDocument
from .delete_file import DeleteFile
from .discard_tag import DiscardTag
from .discover_direct_children import DiscoverDirectChildren
from .discover_whiteboard_view import DiscoverWhiteboardView
from .drop_whiteboard_view import DropWhiteboardView
from .escalate_to_human import EscalateToHuman
from .fetch_descendant_document import FetchDescendantDocument
from .get_access_permission import GetAccessPermission
from .get_datatype import GetDatatype
from .grant_access_permission import GrantAccessPermission
from .insert_datatype import InsertDatatype
from .insert_document import InsertDocument
from .insert_file import InsertFile
from .insert_tags import InsertTags
from .insert_whiteboard_view import InsertWhiteboardView
from .modify_access_permission import ModifyAccessPermission
from .publish_document_version import PublishDocumentVersion
from .remove_datatype import RemoveDatatype
from .remove_document_version import RemoveDocumentVersion
from .remove_embed_block import RemoveEmbedBlock
from .retrieve_document import RetrieveDocument
from .retrieve_entity_by_type import RetrieveEntityByType
from .retrieve_user_info import RetrieveUserInfo
from .retrieve_workspace import RetrieveWorkspace

ALL_TOOLS_INTERFACE_3 = [
    AlterDatatype,
    AlterDocument,
    AlterEmbedBlock,
    AlterFile,
    AlterTags,
    AlterWhiteboardView,
    AttainDocumentParentHierarchy,
    CollectDocumentVersions,
    CreateEmbedBlock,
    DeleteDocument,
    DeleteFile,
    DiscardTag,
    DiscoverDirectChildren,
    DiscoverWhiteboardView,
    DropWhiteboardView,
    EscalateToHuman,
    FetchDescendantDocument,
    GetAccessPermission,
    GetDatatype,
    GrantAccessPermission,
    InsertDatatype,
    InsertDocument,
    InsertFile,
    InsertTags,
    InsertWhiteboardView,
    ModifyAccessPermission,
    PublishDocumentVersion,
    RemoveDatatype,
    RemoveDocumentVersion,
    RemoveEmbedBlock,
    RetrieveDocument,
    RetrieveEntityByType,
    RetrieveUserInfo,
    RetrieveWorkspace
]
