from flask import Blueprint, render_template


databricks_bp = Blueprint("databricks", __name__)


@databricks_bp.route("/databricks", strict_slashes=False, methods=["GET"])
def databricks():
    """Render the Databricks command builder page."""
    return render_template("databricks.html")
