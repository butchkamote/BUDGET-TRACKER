from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Add currency formatter filter for templates
def format_currency(value):
    try:
        return f"₱{float(value):,.2f}"
    except (TypeError, ValueError):
        return "₱0.00"

app.jinja_env.filters['currency'] = format_currency

# Dummy storage: single global savings_goal plus per-cutoff data
data = {
    "15th": {"salary": 0, "bills": []},
    "30th": {"salary": 0, "bills": []},
    "savings_goal": {"name": "", "amount": 0.0, "goal_covered": 0.0}
}


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Salary/bill update
        cutoff = request.form.get("cutoff")
        if cutoff in ("15th", "30th"):
            salary = request.form.get("salary")
            if salary:
                try:
                    data[cutoff]["salary"] = float(salary)
                except ValueError:
                    data[cutoff]["salary"] = 0.0
            new_name = request.form.get("bill_name")
            new_amount = request.form.get("bill_amount")
            if new_name and new_amount:
                try:
                    amt = float(new_amount)
                except ValueError:
                    amt = 0.0
                data[cutoff]["bills"].append({"name": new_name, "amount": amt})

        # Global savings goal update
        goal_name = request.form.get("goal_name")
        goal_amount = request.form.get("goal_amount")
        if goal_name is not None or goal_amount is not None:
            name = goal_name.strip() if goal_name else ""
            try:
                amt = float(goal_amount) if goal_amount not in (None, "") else 0.0
            except ValueError:
                amt = 0.0
            data["savings_goal"]["name"] = name
            data["savings_goal"]["amount"] = amt

        # Handle manual contribution to goal
        if "contrib_15th" in request.form or "contrib_30th" in request.form:
            c15 = request.form.get("contrib_15th")
            c30 = request.form.get("contrib_30th")
            try:
                c15 = float(c15) if c15 else 0.0
            except ValueError:
                c15 = 0.0
            try:
                c30 = float(c30) if c30 else 0.0
            except ValueError:
                c30 = 0.0

            # Calculate available money left for each cutoff
            for cutoff in ("15th", "30th"):
                total_bills = sum(b.get("amount", 0) for b in data[cutoff]["bills"])
                savings_percent = 20
                future_fund = data[cutoff]["salary"] * (savings_percent / 100)
                money_left = data[cutoff]["salary"] - total_bills - future_fund
                # Cap contribution to available money left
                if cutoff == "15th":
                    actual_c15 = min(c15, max(money_left, 0))
                    data[cutoff]["manual_contrib"] = actual_c15
                    data[cutoff]["salary"] -= actual_c15
                    data["savings_goal"]["goal_covered"] += actual_c15
                elif cutoff == "30th":
                    actual_c30 = min(c30, max(money_left, 0))
                    data[cutoff]["manual_contrib"] = actual_c30
                    data[cutoff]["salary"] -= actual_c30
                    data["savings_goal"]["goal_covered"] += actual_c30

    # Calculate results per cutoff
    results = {}
    for cutoff, info in data.items():
        if cutoff == "savings_goal":
            continue
        total_bills = sum(b.get("amount", 0) for b in info.get("bills", []))
        savings_percent = 20
        future_fund = info.get("salary", 0) * (savings_percent / 100)
        money_left = info.get("salary", 0) - total_bills - future_fund
        manual_contrib = info.get("manual_contrib", 0.0)
        results[cutoff] = {
            "salary": info.get("salary", 0),
            "bills": info.get("bills", []),
            "total_bills": total_bills,
            "future_fund": future_fund,
            "flex_money": money_left,
            "manual_contrib": manual_contrib
        }

    total_future = sum(entry["future_fund"] for entry in results.values())
    total_flex = sum(entry["flex_money"] for entry in results.values())

    goal_name = data["savings_goal"].get("name", "")
    goal_amount = float(data["savings_goal"].get("amount", 0.0) or 0.0)
    goal_covered = float(data["savings_goal"].get("goal_covered", 0.0) or 0.0)
    goal_remaining = max(goal_amount - goal_covered, 0.0)

    return render_template(
        "index.html",
        results=results,
        total_future=total_future,
        total_flex=total_flex,
        savings_goal=data["savings_goal"],
        goal_covered=goal_covered,
        goal_remaining=goal_remaining
    )


@app.route("/delete/<cutoff>/<int:bill_id>")
def delete(cutoff, bill_id):
    if cutoff in data and 0 <= bill_id < len(data[cutoff]["bills"]):
        data[cutoff]["bills"].pop(bill_id)
    return redirect(url_for("index"))


@app.route("/delete_goal")
def delete_goal():
    data["savings_goal"] = {"name": "", "amount": 0.0, "goal_covered": 0.0}
    for cutoff in ("15th", "30th"):
        data[cutoff]["manual_contrib"] = 0.0
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
