from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Dummy storage
data = {
    "15th": {"salary": 0, "bills": []},
    "30th": {"salary": 0, "bills": []}
}


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        cutoff = request.form.get("cutoff")

        # Update salary
        salary = request.form.get("salary")
        if salary:
            data[cutoff]["salary"] = float(salary)

        # Add new bill
        new_name = request.form.get("bill_name")
        new_amount = request.form.get("bill_amount")
        if new_name and new_amount:
            data[cutoff]["bills"].append({"name": new_name, "amount": float(new_amount)})

    # Calculate results per cutoff
    results = {}
    for cutoff, info in data.items():
        total_bills = sum(b["amount"] for b in info["bills"])
        future_fund = info["salary"] * 0.20
        flex_money = info["salary"] - total_bills - future_fund
        results[cutoff] = {
            "salary": info["salary"],
            "bills": info["bills"],
            "total_bills": total_bills,
            "future_fund": future_fund,
            "flex_money": flex_money
        }

    # Monthly totals
    total_future = results["15th"]["future_fund"] + results["30th"]["future_fund"]
    total_flex = results["15th"]["flex_money"] + results["30th"]["flex_money"]

    return render_template("index.html", results=results, total_future=total_future, total_flex=total_flex)


@app.route("/delete/<cutoff>/<int:bill_id>")
def delete(cutoff, bill_id):
    if cutoff in data and 0 <= bill_id < len(data[cutoff]["bills"]):
        data[cutoff]["bills"].pop(bill_id)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
