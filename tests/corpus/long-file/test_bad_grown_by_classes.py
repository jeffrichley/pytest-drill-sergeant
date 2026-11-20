# expect: DS106
"""Tests for the lending library: an agent kept adding a class per feature to one
file until it passed 500 lines, pasting setup between tests as it went (DS501). The
file is what DS106 is about. Analysed, never run."""

from datetime import date, timedelta

import pytest
from library import Library, LoanError, Member, ReservationError

OPENING_DAY = date(2026, 1, 5)


@pytest.fixture
def library():
    lib = Library(opened=OPENING_DAY, loan_days=21, daily_fine=25)
    lib.add_book(isbn="978-0-13-468599-1", title="The Pragmatic Programmer")
    lib.add_book(isbn="978-0-201-63361-0", title="Design Patterns")
    lib.add_book(isbn="978-0-262-03384-8", title="Introduction to Algorithms")
    return lib


@pytest.fixture
def member(library):
    return library.join(Member(name="Ada Lovelace", email="ada@example.com"))


class TestCatalogSearch:
    """Searching the catalog by title, author and ISBN."""

    def test_finds_a_book_by_exact_title(self, library):
        """An exact title match returns that one book."""
        results = library.search(title="Design Patterns")

        assert [book.isbn for book in results] == ["978-0-201-63361-0"]

    def test_title_search_ignores_case(self, library):
        """Readers type in any case; the catalog shouldn't care."""
        results = library.search(title="design PATTERNS")

        assert [book.title for book in results] == ["Design Patterns"]

    def test_title_search_matches_a_word_inside_the_title(self, library):
        """A single word finds every title containing it."""
        results = library.search(title="programmer")

        assert [book.title for book in results] == ["The Pragmatic Programmer"]

    def test_search_by_isbn_ignores_hyphens(self, library):
        """ISBNs are printed with and without hyphens."""
        results = library.search(isbn="9780262033848")

        assert [book.title for book in results] == ["Introduction to Algorithms"]

    def test_unknown_title_finds_nothing(self, library):
        """A title the library doesn't hold returns an empty list, not an error."""
        assert library.search(title="Snow Crash") == []

    def test_results_are_sorted_by_title(self, library):
        """Several matches come back in title order."""
        results = library.search(title="i")

        assert [book.title for book in results] == [
            "Design Patterns",
            "Introduction to Algorithms",
            "The Pragmatic Programmer",
        ]

    def test_search_rejects_an_empty_query(self, library):
        """An empty query is a mistake in the caller, so it raises."""
        with pytest.raises(ValueError, match="empty query"):
            library.search(title="")

    def test_withdrawn_books_are_not_found(self, library):
        """A withdrawn book stays in the records but leaves the catalog."""
        library.withdraw("978-0-201-63361-0")

        assert library.search(title="Design Patterns") == []


class TestLoans:
    """Borrowing and returning books."""

    def test_borrowing_marks_the_book_on_loan(self, library, member):
        """A borrowed book is no longer available to others."""
        library.lend("978-0-13-468599-1", to=member, on=OPENING_DAY)

        assert library.is_available("978-0-13-468599-1") is False

    def test_a_loan_is_due_after_the_loan_period(self, library, member):
        """The due date is the loan day plus the library's loan period."""
        loan = library.lend("978-0-13-468599-1", to=member, on=OPENING_DAY)

        assert loan.due == date(2026, 1, 26)

    def test_returning_makes_the_book_available_again(self, library, member):
        """Once returned, the book can be borrowed by someone else."""
        loan = library.lend("978-0-201-63361-0", to=member, on=OPENING_DAY)
        library.receive(loan, on=OPENING_DAY + timedelta(days=3))

        assert library.is_available("978-0-201-63361-0") is True

    def test_cannot_borrow_a_book_already_on_loan(self, library, member):
        """Two members can't hold the same copy."""
        other = library.join(Member(name="Grace Hopper", email="grace@example.com"))
        library.lend("978-0-201-63361-0", to=member, on=OPENING_DAY)

        with pytest.raises(LoanError, match="already on loan"):
            library.lend("978-0-201-63361-0", to=other, on=OPENING_DAY)

    def test_member_loan_limit_is_enforced(self, library, member):
        """A member may hold at most two books at once."""
        library.lend("978-0-13-468599-1", to=member, on=OPENING_DAY)
        library.lend("978-0-201-63361-0", to=member, on=OPENING_DAY)

        with pytest.raises(LoanError, match="loan limit"):
            library.lend("978-0-262-03384-8", to=member, on=OPENING_DAY)

    def test_renewal_extends_the_due_date_by_one_period(self, library, member):
        """Renewing on time adds another full loan period."""
        loan = library.lend("978-0-13-468599-1", to=member, on=OPENING_DAY)
        renewed = library.renew(loan, on=date(2026, 1, 20))

        assert renewed.due == date(2026, 2, 16)

    def test_an_overdue_loan_cannot_be_renewed(self, library, member):
        """Renewal after the due date is refused; the book must come back."""
        loan = library.lend("978-0-13-468599-1", to=member, on=OPENING_DAY)

        with pytest.raises(LoanError, match="overdue"):
            library.renew(loan, on=date(2026, 2, 1))

    def test_loan_history_lists_returned_loans_oldest_first(self, library, member):
        """A member's history keeps every loan they have returned."""
        first = library.lend("978-0-13-468599-1", to=member, on=OPENING_DAY)
        library.receive(first, on=date(2026, 1, 10))
        second = library.lend("978-0-201-63361-0", to=member, on=date(2026, 1, 11))
        library.receive(second, on=date(2026, 1, 15))

        assert [loan.isbn for loan in library.history(member)] == [
            "978-0-13-468599-1",
            "978-0-201-63361-0",
        ]


class TestFines:
    """Fines for late returns."""

    def test_on_time_return_has_no_fine(self, library, member):
        """Returning on the due date costs nothing."""
        loan = library.lend("978-0-13-468599-1", to=member, on=OPENING_DAY)

        receipt = library.receive(loan, on=loan.due)

        assert receipt.fine == 0

    def test_fine_is_charged_per_day_late(self, library, member):
        """Each day past the due date adds the daily fine."""
        loan = library.lend("978-0-13-468599-1", to=member, on=OPENING_DAY)

        receipt = library.receive(loan, on=loan.due + timedelta(days=4))

        assert receipt.fine == 100

    def test_fine_is_capped_at_the_replacement_cost(self, library, member):
        """A book returned months late costs no more than replacing it."""
        library.set_replacement_cost("978-0-13-468599-1", 3000)
        loan = library.lend("978-0-13-468599-1", to=member, on=OPENING_DAY)

        receipt = library.receive(loan, on=loan.due + timedelta(days=365))

        assert receipt.fine == 3000

    def test_unpaid_fines_accumulate_on_the_account(self, library, member):
        """Two late returns add up on the member's balance."""
        first = library.lend("978-0-13-468599-1", to=member, on=OPENING_DAY)
        library.receive(first, on=first.due + timedelta(days=2))
        second = library.lend("978-0-201-63361-0", to=member, on=OPENING_DAY)
        library.receive(second, on=second.due + timedelta(days=1))

        assert library.balance(member) == 75

    def test_paying_clears_the_balance(self, library, member):
        """A payment equal to the balance leaves nothing owing."""
        loan = library.lend("978-0-13-468599-1", to=member, on=OPENING_DAY)
        library.receive(loan, on=loan.due + timedelta(days=2))

        library.pay(member, amount=50)

        assert library.balance(member) == 0

    def test_overpaying_is_refused(self, library, member):
        """The library doesn't hold credit; paying too much is an error."""
        with pytest.raises(ValueError, match="more than is owed"):
            library.pay(member, amount=10)

    def test_members_owing_too_much_cannot_borrow(self, library, member):
        """A balance over the limit blocks new loans until it is paid."""
        loan = library.lend("978-0-13-468599-1", to=member, on=OPENING_DAY)
        library.receive(loan, on=loan.due + timedelta(days=30))

        with pytest.raises(LoanError, match="outstanding fines"):
            library.lend("978-0-201-63361-0", to=member, on=date(2026, 3, 1))

    def test_waived_fine_leaves_a_note_on_the_account(self, library, member):
        """Staff can waive a fine, and the waiver is recorded with its reason."""
        loan = library.lend("978-0-13-468599-1", to=member, on=OPENING_DAY)
        receipt = library.receive(loan, on=loan.due + timedelta(days=3))

        library.waive(receipt, reason="branch closed for snow")

        assert library.notes(member) == ["fine of 75 waived: branch closed for snow"]


class TestReservations:
    """Reserving books that are on loan."""

    def test_reserving_a_book_on_loan_queues_the_member(self, library, member):
        """A reservation puts the member in the book's queue."""
        other = library.join(  # expect: DS501
            Member(name="Grace Hopper", email="grace@example.com")
        )
        library.lend("978-0-201-63361-0", to=other, on=OPENING_DAY)

        library.reserve("978-0-201-63361-0", for_member=member)

        assert library.queue("978-0-201-63361-0") == [member]

    def test_cannot_reserve_an_available_book(self, library, member):
        """An available book should simply be borrowed."""
        with pytest.raises(ReservationError, match="is available"):
            library.reserve("978-0-201-63361-0", for_member=member)

    def test_returned_book_is_held_for_the_first_in_queue(self, library, member):
        """On return, the book is held for the next reader instead of shelved."""
        other = library.join(Member(name="Grace Hopper", email="grace@example.com"))
        loan = library.lend("978-0-201-63361-0", to=other, on=OPENING_DAY)
        library.reserve("978-0-201-63361-0", for_member=member)

        library.receive(loan, on=date(2026, 1, 12))

        assert library.held_for("978-0-201-63361-0") == member

    def test_a_hold_expires_after_seven_days(self, library, member):
        """A hold nobody collects goes to the next reader after a week."""
        other = library.join(Member(name="Grace Hopper", email="grace@example.com"))
        third = library.join(Member(name="Alan Turing", email="alan@example.com"))
        loan = library.lend("978-0-201-63361-0", to=other, on=OPENING_DAY)
        library.reserve("978-0-201-63361-0", for_member=member)
        library.reserve("978-0-201-63361-0", for_member=third)
        library.receive(loan, on=date(2026, 1, 12))

        library.expire_holds(on=date(2026, 1, 20))

        assert library.held_for("978-0-201-63361-0") == third

    def test_cancelling_a_reservation_leaves_the_queue(self, library, member):
        """A member who changes their mind is removed from the queue."""
        other = library.join(Member(name="Grace Hopper", email="grace@example.com"))
        library.lend("978-0-201-63361-0", to=other, on=OPENING_DAY)
        library.reserve("978-0-201-63361-0", for_member=member)

        library.cancel_reservation("978-0-201-63361-0", for_member=member)

        assert library.queue("978-0-201-63361-0") == []

    def test_one_member_cannot_reserve_twice(self, library, member):
        """The queue holds each member at most once."""
        other = library.join(Member(name="Grace Hopper", email="grace@example.com"))
        library.lend("978-0-201-63361-0", to=other, on=OPENING_DAY)
        library.reserve("978-0-201-63361-0", for_member=member)

        with pytest.raises(ReservationError, match="already reserved"):
            library.reserve("978-0-201-63361-0", for_member=member)


class TestMemberAccounts:
    """Joining, updating and leaving the library."""

    def test_joining_assigns_a_card_number(self, library):
        """Every new member gets the next card number."""
        member = library.join(Member(name="Alan Turing", email="alan@example.com"))

        assert member.card == "C-0001"

    def test_card_numbers_increase_in_join_order(self, library):
        """The second member's card follows the first's."""
        library.join(Member(name="Alan Turing", email="alan@example.com"))
        second = library.join(Member(name="Grace Hopper", email="grace@example.com"))

        assert second.card == "C-0002"

    def test_email_must_be_unique(self, library, member):
        """Two members can't share an email address."""
        with pytest.raises(ValueError, match="already registered"):
            library.join(Member(name="Someone Else", email="ada@example.com"))

    def test_updating_email_keeps_the_card(self, library, member):
        """A change of address doesn't change who the member is."""
        library.update(member, email="countess@example.com")

        assert library.find(card=member.card).email == "countess@example.com"

    def test_member_with_loans_cannot_leave(self, library, member):
        """Leaving is refused while books are still out."""
        library.lend("978-0-13-468599-1", to=member, on=OPENING_DAY)

        with pytest.raises(LoanError, match="books on loan"):
            library.leave(member)

    def test_leaving_removes_the_member(self, library, member):
        """A member with nothing out can leave, and is no longer found."""
        library.leave(member)

        assert library.find(card=member.card) is None

    def test_leaving_cancels_reservations(self, library, member):
        """A departing member's place in every queue is given up."""
        other = library.join(Member(name="Grace Hopper", email="grace@example.com"))
        library.lend("978-0-262-03384-8", to=other, on=OPENING_DAY)
        library.reserve("978-0-262-03384-8", for_member=member)

        library.leave(member)

        assert library.queue("978-0-262-03384-8") == []


class TestOpeningHours:
    """When the library is open, and what that does to due dates."""

    def test_open_on_a_weekday(self, library):
        """Monday to Friday the doors are open."""
        assert library.is_open(on=date(2026, 1, 7)) is True

    def test_closed_on_sunday(self, library):
        """Sunday is the one closed day."""
        assert library.is_open(on=date(2026, 1, 11)) is False

    def test_due_date_on_a_closed_day_moves_to_the_next_open_day(self, library, member):
        """A loan can't fall due on a day nobody can return it."""
        loan = library.lend("978-0-13-468599-1", to=member, on=date(2026, 1, 11))

        assert loan.due == date(2026, 2, 2)

    def test_public_holidays_are_closed(self, library):
        """Holidays added by staff close the library for the day."""
        library.add_holiday(date(2026, 5, 4))

        assert library.is_open(on=date(2026, 5, 4)) is False

    def test_no_fines_accrue_on_closed_days(self, library, member):
        """A reader isn't fined for days the library was shut."""
        library.add_holiday(date(2026, 1, 27))
        loan = library.lend("978-0-13-468599-1", to=member, on=OPENING_DAY)

        receipt = library.receive(loan, on=date(2026, 1, 28))

        assert receipt.fine == 25


class TestReports:
    """The monthly reports staff print for the board."""

    def test_most_borrowed_lists_titles_by_loan_count(self, library, member):
        """The busiest title comes first."""
        for day in (5, 9, 13):
            loan = library.lend("978-0-201-63361-0", to=member, on=date(2026, 1, day))
            library.receive(loan, on=date(2026, 1, day + 1))

        report = library.report(month="2026-01")

        assert report.most_borrowed[0] == ("Design Patterns", 3)

    def test_report_counts_new_members(self, library):
        """Members who joined in the month are counted."""
        library.join(Member(name="Alan Turing", email="alan@example.com"))
        library.join(Member(name="Grace Hopper", email="grace@example.com"))

        report = library.report(month="2026-01")

        assert report.new_members == 2

    def test_report_totals_fines_collected(self, library, member):
        """Only fines actually paid count as collected."""
        loan = library.lend("978-0-13-468599-1", to=member, on=OPENING_DAY)
        library.receive(loan, on=loan.due + timedelta(days=2))
        library.pay(member, amount=50)

        report = library.report(month="2026-01")

        assert report.fines_collected == 50

    def test_report_for_a_month_before_opening_is_refused(self, library):
        """There is nothing to report before the library existed."""
        with pytest.raises(ValueError, match="before opening"):
            library.report(month="2025-12")


class TestNotifications:
    """The emails the library sends to members."""

    def test_reminder_is_sent_two_days_before_the_due_date(self, library, member):
        """A gentle reminder goes out before a loan falls due."""
        loan = library.lend("978-0-13-468599-1", to=member, on=OPENING_DAY)

        sent = library.send_reminders(on=loan.due - timedelta(days=2))

        assert [(mail.to, mail.subject) for mail in sent] == [
            ("ada@example.com", "Due soon: The Pragmatic Programmer")
        ]

    def test_no_reminder_for_a_returned_book(self, library, member):
        """A book already back needs no reminder."""
        loan = library.lend("978-0-13-468599-1", to=member, on=OPENING_DAY)
        library.receive(loan, on=date(2026, 1, 8))

        assert library.send_reminders(on=loan.due - timedelta(days=2)) == []

    def test_overdue_notice_names_the_fine_so_far(self, library, member):
        """The overdue email tells the member what they owe today."""
        loan = library.lend("978-0-13-468599-1", to=member, on=OPENING_DAY)

        [notice] = library.send_overdue_notices(on=loan.due + timedelta(days=6))

        assert notice.fine == 150

    def test_hold_notice_goes_to_the_member_it_is_held_for(self, library, member):
        """When a reserved book comes in, its reader hears about it."""
        other = library.join(Member(name="Grace Hopper", email="grace@example.com"))
        loan = library.lend("978-0-201-63361-0", to=other, on=OPENING_DAY)
        library.reserve("978-0-201-63361-0", for_member=member)

        library.receive(loan, on=date(2026, 1, 12))

        assert library.outbox()[-1].to == "ada@example.com"

    def test_members_who_opt_out_get_no_reminders(self, library, member):
        """Reminders respect the member's mail preference."""
        library.update(member, reminders=False)
        loan = library.lend("978-0-13-468599-1", to=member, on=OPENING_DAY)

        assert library.send_reminders(on=loan.due - timedelta(days=2)) == []


class TestInterLibraryLoans:
    """Borrowing books the library doesn't hold from partner libraries."""

    def test_request_is_sent_to_the_partner_that_holds_the_book(self, library, member):
        """The request goes to the partner whose catalog lists the ISBN."""
        library.add_partner("Northgate", holds=["978-0-596-51774-8"])

        request = library.request_from_partner("978-0-596-51774-8", for_member=member)

        assert request.partner == "Northgate"

    def test_request_for_a_book_nobody_holds_is_refused(self, library, member):
        """With no partner holding it, there is nowhere to ask."""
        with pytest.raises(LoanError, match="no partner holds"):
            library.request_from_partner("978-1-4919-5017-9", for_member=member)

    def test_partner_loans_have_a_shorter_period(self, library, member):
        """Books from partners are lent for fourteen days, not twenty-one."""
        library.add_partner("Northgate", holds=["978-0-596-51774-8"])  # expect: DS501
        request = library.request_from_partner("978-0-596-51774-8", for_member=member)
        library.arrive(request, on=date(2026, 1, 9))

        loan = library.lend_partner_copy(request, on=date(2026, 1, 10))

        assert loan.due == date(2026, 1, 24)

    def test_partner_loans_cannot_be_renewed(self, library, member):
        """The partner wants its book back on time."""
        library.add_partner("Northgate", holds=["978-0-596-51774-8"])
        request = library.request_from_partner("978-0-596-51774-8", for_member=member)
        library.arrive(request, on=date(2026, 1, 9))
        loan = library.lend_partner_copy(request, on=date(2026, 1, 10))

        with pytest.raises(LoanError, match="partner copy"):
            library.renew(loan, on=date(2026, 1, 20))

    def test_returned_partner_copy_is_sent_back(self, library, member):
        """A returned partner book goes into the outgoing crate, not the shelf."""
        library.add_partner("Northgate", holds=["978-0-596-51774-8"])
        request = library.request_from_partner("978-0-596-51774-8", for_member=member)
        library.arrive(request, on=date(2026, 1, 9))
        loan = library.lend_partner_copy(request, on=date(2026, 1, 10))

        library.receive(loan, on=date(2026, 1, 20))

        assert library.outgoing_crate("Northgate") == ["978-0-596-51774-8"]

    def test_partner_requests_count_against_the_loan_limit(self, library, member):
        """A pending partner request takes one of the member's two slots."""
        library.add_partner("Northgate", holds=["978-0-596-51774-8"])
        library.request_from_partner("978-0-596-51774-8", for_member=member)
        library.lend("978-0-13-468599-1", to=member, on=OPENING_DAY)

        with pytest.raises(LoanError, match="loan limit"):
            library.lend("978-0-201-63361-0", to=member, on=OPENING_DAY)

    def test_cancelled_request_frees_the_slot(self, library, member):
        """Cancelling a partner request gives the member their slot back."""
        library.add_partner("Northgate", holds=["978-0-596-51774-8"])
        request = library.request_from_partner("978-0-596-51774-8", for_member=member)

        library.cancel_request(request)

        assert library.slots_free(member) == 2
