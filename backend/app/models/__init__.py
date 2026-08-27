# Import all models here so Base.metadata sees them for Alembic autogenerate.
from app.models.user import User  # noqa: F401
from app.models.connected_account import ConnectedAccount  # noqa: F401
from app.models.source_video import SourceVideo  # noqa: F401
from app.models.processing_job import ProcessingJob  # noqa: F401
from app.models.clip import Clip  # noqa: F401
from app.models.brand_template import BrandTemplate  # noqa: F401
from app.models.publish_job import PublishJob  # noqa: F401
from app.models.credit_transaction import CreditTransaction  # noqa: F401
