(() => {
  const roots = document.querySelectorAll("[data-booking-search]");
  if (!roots.length) return;

  const dayFormatter = new Intl.DateTimeFormat("pl-PL", {
    day: "numeric",
    month: "short",
  });
  const fullDateFormatter = new Intl.DateTimeFormat("pl-PL", {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
  const monthFormatter = new Intl.DateTimeFormat("pl-PL", {
    month: "long",
    year: "numeric",
  });
  const weekdayLabels = ["Pn", "Wt", "Sr", "Cz", "Pt", "So", "Nd"];

  function dateOnly(value) {
    if (!value) return null;
    const parts = value.split("-").map(Number);
    if (parts.length !== 3 || parts.some(Number.isNaN)) return null;
    return new Date(parts[0], parts[1] - 1, parts[2]);
  }

  function toISO(value) {
    const year = value.getFullYear();
    const month = String(value.getMonth() + 1).padStart(2, "0");
    const day = String(value.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  function startOfDay(value) {
    return new Date(value.getFullYear(), value.getMonth(), value.getDate());
  }

  function addMonths(value, amount) {
    return new Date(value.getFullYear(), value.getMonth() + amount, 1);
  }

  function sameDay(left, right) {
    return Boolean(left && right && left.getTime() === right.getTime());
  }

  roots.forEach(root => {
    const form = root.querySelector("form");
    const checkInInput = root.querySelector("[data-booking-check-in]");
    const checkOutInput = root.querySelector("[data-booking-check-out]");
    const checkInLabel = root.querySelector("[data-booking-check-in-label]");
    const checkOutLabel = root.querySelector("[data-booking-check-out-label]");
    const dateTriggers = root.querySelectorAll("[data-booking-date-trigger]");
    const calendar = root.querySelector("[data-booking-calendar]");
    const monthsElement = root.querySelector("[data-booking-months]");
    const selectionElement = root.querySelector("[data-booking-selection]");
    const nightsElement = root.querySelector("[data-booking-nights]");
    const previousButton = root.querySelector("[data-booking-month-prev]");
    const nextButton = root.querySelector("[data-booking-month-next]");
    const calendarClose = root.querySelector("[data-booking-calendar-close]");
    const guestsTrigger = root.querySelector("[data-booking-guests-trigger]");
    const guestsPopover = root.querySelector("[data-booking-guests-popover]");
    const guestsClose = root.querySelector("[data-booking-guests-close]");
    const guestsInput = root.querySelector("[data-booking-guests]");
    const roomsInput = root.querySelector("[data-booking-rooms]");
    const guestsCount = root.querySelector("[data-booking-guests-count]");
    const roomsCount = root.querySelector("[data-booking-rooms-count]");
    const guestsLabel = root.querySelector("[data-booking-guests-label]");
    const errorElement = root.querySelector("[data-booking-error]");
    const today = startOfDay(new Date());
    const maxRooms = Math.max(1, Number(root.dataset.maxRooms) || 4);

    let checkIn = dateOnly(checkInInput.value);
    let checkOut = dateOnly(checkOutInput.value);
    let visibleMonth = new Date(
      (checkIn || today).getFullYear(),
      (checkIn || today).getMonth(),
      1,
    );
    let guests = Math.min(12, Math.max(1, Number(guestsInput.value) || 2));
    let rooms = Math.min(maxRooms, Math.max(1, Number(roomsInput.value) || 1));

    function nightsCount() {
      if (!checkIn || !checkOut) return 0;
      return Math.round((checkOut - checkIn) / 86400000);
    }

    function updateDateLabels() {
      checkInInput.value = checkIn ? toISO(checkIn) : "";
      checkOutInput.value = checkOut ? toISO(checkOut) : "";
      checkInLabel.textContent = checkIn ? dayFormatter.format(checkIn) : "Wybierz date";
      checkOutLabel.textContent = checkOut ? dayFormatter.format(checkOut) : "Wybierz date";

      if (!checkIn) {
        selectionElement.textContent = "Wybierz date przyjazdu";
        nightsElement.textContent = "Wybierz termin pobytu";
      } else if (!checkOut) {
        selectionElement.textContent = `${fullDateFormatter.format(checkIn)} - wybierz wyjazd`;
        nightsElement.textContent = "Wybierz date wyjazdu";
      } else {
        const nights = nightsCount();
        selectionElement.textContent = `${fullDateFormatter.format(checkIn)} - ${fullDateFormatter.format(checkOut)}`;
        nightsElement.textContent = `${nights} ${nights === 1 ? "noc" : "nocy"}`;
      }
      calendarClose.disabled = !checkIn || !checkOut;
    }

    function updateGuests() {
      if (rooms > guests) guests = rooms;
      guestsInput.value = String(guests);
      roomsInput.value = String(rooms);
      guestsCount.textContent = String(guests);
      roomsCount.textContent = String(rooms);
      guestsLabel.textContent = `${guests} ${guests === 1 ? "gosc" : "gosci"}, ${rooms} ${rooms === 1 ? "apartament" : "apartamenty"}`;
    }

    function renderMonth(monthDate) {
      const month = document.createElement("section");
      month.className = "booking-calendar-month";

      const title = document.createElement("h3");
      title.textContent = monthFormatter.format(monthDate);
      month.appendChild(title);

      const weekdays = document.createElement("div");
      weekdays.className = "booking-calendar-weekdays";
      weekdayLabels.forEach(label => {
        const item = document.createElement("span");
        item.textContent = label;
        weekdays.appendChild(item);
      });
      month.appendChild(weekdays);

      const days = document.createElement("div");
      days.className = "booking-calendar-days";
      const firstDay = new Date(monthDate.getFullYear(), monthDate.getMonth(), 1);
      const leadingDays = (firstDay.getDay() + 6) % 7;
      const daysInMonth = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0).getDate();
      const cellCount = Math.ceil((leadingDays + daysInMonth) / 7) * 7;

      for (let cell = 0; cell < cellCount; cell += 1) {
        const dayNumber = cell - leadingDays + 1;
        const button = document.createElement("button");
        button.type = "button";
        button.className = "booking-calendar-day";

        if (dayNumber < 1 || dayNumber > daysInMonth) {
          button.classList.add("is-outside");
          button.disabled = true;
          days.appendChild(button);
          continue;
        }

        const day = new Date(monthDate.getFullYear(), monthDate.getMonth(), dayNumber);
        button.textContent = String(dayNumber);
        button.dataset.date = toISO(day);
        button.setAttribute("aria-label", fullDateFormatter.format(day));
        button.disabled = day < today;

        if (sameDay(day, today)) button.classList.add("is-today");
        if (sameDay(day, checkIn)) button.classList.add("is-start");
        if (sameDay(day, checkOut)) button.classList.add("is-end");
        if (checkIn && checkOut && day > checkIn && day < checkOut) {
          button.classList.add("is-range");
        }

        button.addEventListener("click", () => selectDate(day));
        days.appendChild(button);
      }

      month.appendChild(days);
      return month;
    }

    function renderCalendar() {
      monthsElement.replaceChildren(
        renderMonth(visibleMonth),
        renderMonth(addMonths(visibleMonth, 1)),
      );
      const currentMonth = new Date(today.getFullYear(), today.getMonth(), 1);
      previousButton.disabled = visibleMonth <= currentMonth;
      updateDateLabels();
    }

    function selectDate(day) {
      errorElement.hidden = true;
      if (!checkIn || checkOut) {
        checkIn = day;
        checkOut = null;
      } else if (day <= checkIn) {
        checkIn = day;
      } else {
        checkOut = day;
      }
      renderCalendar();
    }

    function closeCalendar() {
      calendar.hidden = true;
      dateTriggers.forEach(trigger => trigger.setAttribute("aria-expanded", "false"));
    }

    function openCalendar(preferredField) {
      guestsPopover.hidden = true;
      guestsTrigger.setAttribute("aria-expanded", "false");
      calendar.hidden = false;
      dateTriggers.forEach(trigger => trigger.setAttribute("aria-expanded", "true"));
      if (preferredField === "check_in" && checkIn) {
        visibleMonth = new Date(checkIn.getFullYear(), checkIn.getMonth(), 1);
      } else if (preferredField === "check_out" && checkOut) {
        visibleMonth = new Date(checkOut.getFullYear(), checkOut.getMonth(), 1);
      }
      renderCalendar();
    }

    dateTriggers.forEach(trigger => {
      trigger.addEventListener("click", () => {
        if (!calendar.hidden) closeCalendar();
        else openCalendar(trigger.dataset.bookingDateTrigger);
      });
    });

    previousButton.addEventListener("click", () => {
      visibleMonth = addMonths(visibleMonth, -1);
      renderCalendar();
    });

    nextButton.addEventListener("click", () => {
      visibleMonth = addMonths(visibleMonth, 1);
      renderCalendar();
    });

    calendarClose.addEventListener("click", closeCalendar);

    guestsTrigger.addEventListener("click", () => {
      closeCalendar();
      guestsPopover.hidden = !guestsPopover.hidden;
      guestsTrigger.setAttribute("aria-expanded", String(!guestsPopover.hidden));
    });

    guestsClose.addEventListener("click", () => {
      guestsPopover.hidden = true;
      guestsTrigger.setAttribute("aria-expanded", "false");
    });

    root.querySelectorAll("[data-booking-step]").forEach(button => {
      button.addEventListener("click", () => {
        const delta = Number(button.dataset.delta);
        if (button.dataset.bookingStep === "guests") {
          guests = Math.min(12, Math.max(1, guests + delta));
        } else {
          rooms = Math.min(maxRooms, Math.max(1, rooms + delta));
        }
        updateGuests();
      });
    });

    form.addEventListener("submit", event => {
      if (checkIn && checkOut && checkOut > checkIn) return;
      event.preventDefault();
      errorElement.textContent = "Wybierz date przyjazdu i wyjazdu.";
      errorElement.hidden = false;
      openCalendar(checkIn ? "check_out" : "check_in");
    });

    document.addEventListener("click", event => {
      if (!root.contains(event.target)) {
        closeCalendar();
        guestsPopover.hidden = true;
        guestsTrigger.setAttribute("aria-expanded", "false");
      }
    });

    document.addEventListener("keydown", event => {
      if (event.key !== "Escape") return;
      closeCalendar();
      guestsPopover.hidden = true;
      guestsTrigger.setAttribute("aria-expanded", "false");
    });

    updateGuests();
    renderCalendar();
  });
})();
