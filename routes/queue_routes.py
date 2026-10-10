from flask import Blueprint, render_template, redirect, url_for, flash
from models import office as office_model
from models import token as token_model

queue_bp = Blueprint("queue", __name__)


@queue_bp.route("/")
@queue_bp.route("/display")
def display_root():
    all_offices = office_model.get_all_offices(status="active")
    if not all_offices:
        return render_template("queue/display.html", office=None, offices=[], display_data={"now_serving": [], "waiting_queue": [], "stats": {}})
    return redirect(url_for("queue.display_office", office_id=all_offices[0]["id"]))


@queue_bp.route("/display/<int:office_id>")
def display_office(office_id):
    all_offices = office_model.get_all_offices(status="active")
    selected_office = office_model.get_office_by_id(office_id)
    if not selected_office and all_offices:
        selected_office = all_offices[0]
        office_id = selected_office["id"]

    display_data = token_model.get_office_display_data(office_id) if selected_office else {"now_serving": [], "waiting_queue": [], "stats": {}}

    return render_template(
        "queue/display.html",
        office=selected_office,
        offices=all_offices,
        display_data=display_data,
    )
