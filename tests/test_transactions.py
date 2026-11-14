import copy
from datetime import datetime

import pytest

from transactions import (
    add_transaction,
    delete_transaction,
    rename_in_transactions,
    replace_category,
    sorted_transactions,
    update_transaction,
)

FOOD = {"name": "Food", "color": [1, 0.6, 0.2, 1]}
GAS = {"name": "Gas", "color": [0.3, 0.6, 0.9, 1]}


def make_entry(amount, day, category=None, **details):
    return {"amount": amount, "timestamp": datetime(2026, 10, day, 12, 0), "category": category, "note": None, **details}


@pytest.fixture
def transactions():
    return [
        make_entry(5.0, 1, FOOD, retailer="Walmrat"),
        make_entry(7.0, 2, GAS, retailer="Target"),
        make_entry(9.0, 3),
    ]


## EVERY CHANGE LEAVES THE OLD LIST AS IT WAS ##

@pytest.mark.parametrize("change", [
    lambda t: add_transaction(t, make_entry(1.0, 4)),
    lambda t: update_transaction(t, 0, {"amount": 50.0}),
    lambda t: delete_transaction(t, 1),
    lambda t: rename_in_transactions(t, "retailer", "Walmrat", "Walmart"),
    lambda t: replace_category(t, "Food", {"name": "Groceries", "color": [1, 0.6, 0.2, 1]}),
])
def test_changes_return_a_new_list_and_leave_the_old_one_as_it_was(transactions, change):
    before = copy.deepcopy(transactions)

    changed = change(transactions)

    assert changed is not transactions
    assert transactions == before


## ADD / UPDATE / DELETE ##

def test_add_transaction_puts_it_last(transactions):
    entry = make_entry(1.0, 4)

    assert add_transaction(transactions, entry) == transactions + [entry]


def test_update_transaction_changes_only_the_given_fields_of_one_transaction(transactions):
    updated = update_transaction(transactions, 1, {"amount": 70.0, "note": "fill up"})

    assert updated[1] == {**transactions[1], "amount": 70.0, "note": "fill up"}
    assert updated[0] is transactions[0] and updated[2] is transactions[2]


def test_update_transaction_can_add_fields_an_older_transaction_lacks(transactions):
    updated = update_transaction(transactions, 2, {"retailer": "Aldi", "brand": None})

    assert (updated[2]["retailer"], updated[2]["brand"]) == ("Aldi", None)


def test_delete_transaction_removes_only_that_one(transactions):
    assert delete_transaction(transactions, 1) == [transactions[0], transactions[2]]


@pytest.mark.parametrize("index", [-1, 3, 99])
def test_delete_transaction_outside_the_list_leaves_it_unchanged(transactions, index):
    assert delete_transaction(transactions, index) == transactions


## RENAMING ##

def test_rename_in_transactions_changes_only_matching_names_of_that_kind(transactions):
    transactions[0]["brand"] = "Walmrat"

    renamed = rename_in_transactions(transactions, "retailer", "Walmrat", "Walmart")

    assert [entry.get("retailer") for entry in renamed] == ["Walmart", "Target", None]
    assert renamed[0]["brand"] == "Walmrat"


def test_replace_category_swaps_it_into_every_transaction_that_used_it(transactions):
    groceries = {"name": "Groceries", "color": [0.2, 0.8, 0.2, 1]}

    replaced = replace_category(transactions, "Food", groceries)

    assert [entry["category"] for entry in replaced] == [groceries, GAS, None]


## SORTING ##

def test_sorted_transactions_keeps_only_the_range_with_each_ones_place_in_the_list(transactions):
    pairs = sorted_transactions(transactions, datetime(2026, 10, 2), datetime(2026, 10, 4), "date", True)

    assert [index for index, _ in pairs] == [2, 1]
    assert pairs[0][1] is transactions[2]


def test_sorted_transactions_by_amount_breaks_ties_by_date():
    transactions = [make_entry(5.0, 3), make_entry(9.0, 1), make_entry(5.0, 2)]

    pairs = sorted_transactions(transactions, datetime(2026, 10, 1), datetime(2026, 11, 1), "amount", False)

    assert [index for index, _ in pairs] == [2, 0, 1]
