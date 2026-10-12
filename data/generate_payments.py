from faker import Faker
import pandas as pd
import random


# 1. Setup

fake = Faker("en_IN")
fake.seed_instance(400)
random.seed(400)


# 2. Load treatments
treatments_df = pd.read_csv(
    "data/treatments.csv"
)

treatments_df["start_date"] = pd.to_datetime(
    treatments_df["start_date"]
)

treatments_df["end_date"] = pd.to_datetime(
    treatments_df["end_date"]
)


# 3. Payment methods
payment_methods = [
    "UPI",
    "Credit Card",
    "Debit Card",
    "Net Banking",
    "Cash",
    "Insurance"
]


# 4. Payment statuses
payment_statuses = [
    "Paid",
    "Pending",
    "Failed",
    "Refunded"
]


# 5. Generate payments

payments = []

payment_counter = 1


for _, treatment in treatments_df.iterrows():

    treatment_id = treatment["treatment_id"]
    treatment_cost = int(treatment["estimated_cost"])

    treatment_start = treatment["start_date"]
    treatment_end = treatment["end_date"]
    treatment_status = treatment["status"]

    # Decide number of payments
    if treatment_status == "Cancelled":
        number_of_payments = random.choice([1, 2])

    elif treatment_status == "Completed":
        number_of_payments = random.choice([2, 3, 4])

    else:
        number_of_payments = random.choice([1, 2, 3])


    # Define payment percentages
    if number_of_payments == 1:
        percentages = [1.00]

    elif number_of_payments == 2:
        percentages = [0.40, 0.60]

    elif number_of_payments == 3:
        percentages = [0.30, 0.30, 0.40]

    else:
        percentages = [0.25, 0.25, 0.25, 0.25]


    remaining_amount = treatment_cost

    # Create individual payments


    for payment_number, percentage in enumerate(
        percentages,
        start=1
    ):

        if payment_number == len(percentages):

            # Final payment gets the remaining amount
            amount = remaining_amount

        else:

            amount = round(
                treatment_cost * percentage
            )

            remaining_amount -= amount



        # Generate payment date


        total_days = max(
            (treatment_end - treatment_start).days,
            1
        )

        days_from_start = int(
            (payment_number - 1)
            * total_days
            / len(percentages)
        )

        payment_date = (
            treatment_start
            + pd.Timedelta(
                days=days_from_start
            )
        )

        if payment_date > treatment_end:
            payment_date = treatment_end


        # Determine payment status

        if treatment_status == "Cancelled":

            if payment_number == 1:
                status = random.choice([
                    "Paid",
                    "Refunded"
                ])
            else:
                status = random.choice([
                    "Pending",
                    "Refunded"
                ])

        elif treatment_status == "Completed":

            # Completed treatment usually has
            # completed payments
            status = random.choices(
                ["Paid", "Pending", "Refunded"],
                weights=[90, 8, 2],
                k=1
            )[0]

        else:

            status = random.choices(
                ["Paid", "Pending", "Failed"],
                weights=[75, 20, 5],
                k=1
            )[0]


        payment = {
            "payment_id": f"PAY{payment_counter:06d}",
            "treatment_id": treatment_id,
            "payment_number": payment_number,
            "payment_date": payment_date.date(),
            "amount": amount,
            "payment_method": random.choice(
                payment_methods
            ),
            "status": status,
        }

        payments.append(payment)

        payment_counter += 1


# -----------------------------
# 6. Convert to DataFrame
# -----------------------------
payments_df = pd.DataFrame(payments)


# 7. Save payments

payments_df.to_csv(
    "data/payments.csv",
    index=False
)



# 8. Display results
print(
    "Payments created:",
    len(payments_df)
)

print("\nFirst 10 payments:")
print(
    payments_df.head(10)
)

print("\nColumns:")
print(
    payments_df.columns.tolist()
)

print("\nMissing values:")
print(
    payments_df.isnull().sum()
)
