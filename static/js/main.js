document.addEventListener('DOMContentLoaded', function () {
    profileDropDown();
    removeAlertMessages();

    const bookNowBtn = document.querySelector("#bookNowBtn");
    if (bookNowBtn) {
        bookNowBtn.addEventListener("click", function () {
            const vegPrice = bookNowBtn.getAttribute("data-veg-price");
            const nonVegPrice = bookNowBtn.getAttribute("data-non-veg-price");
            const bookingModal = document.getElementById('bookingModal');

            openModal(bookingModal);
            bookNow(vegPrice, nonVegPrice);
        })
    }

    const swiper = new Swiper('.swiper', {
        direction: 'horizontal',

        slidesPerView: 1,
        breakpoints: {
            640: {
                slidesPerView: 2,
                spaceBetween: 16,
            },
            1024: {
                slidesPerView: 4,
                spaceBetween: 24,
            },
        },
        watchOverflow: true,

        pagination: {
            el: '.swiper-pagination',
            clickable: true,
        },

        navigation: {
            nextEl: '.swiper-button-next',
            prevEl: '.swiper-button-prev',
        },
    });
})


function profileDropDown() {
    const profileContainer = document.querySelector('#profile-dropdown-btn');
    if (profileContainer) {
        profileContainer.addEventListener('click', function () {
            const dropdown = document.querySelector('#profile-dropdown-menu');
            dropdown.classList.toggle('hidden');
            this.parentElement.classList.toggle("bg-secondary");
        });
    }
}

function removeAlertMessages() {
    const messageContainer = document.getElementById('message-container');
    if (messageContainer) {
        const messages = messageContainer.querySelectorAll('[id^="message-"]');
        messages.forEach((message, index) => {
            setTimeout(() => {
                message.classList.remove('opacity-100');
                message.classList.add('opacity-0');
                setTimeout(() => {
                    message.remove();
                }, 1000);
            }, index * 3000);
        });
    }
}

function openModal(modal) {
    let body = document.body;
    modal.classList.remove('hidden');
    body.style.overflow = 'hidden';
    body.style.position = 'fixed';
    body.style.width = '100%';
}

function clearFormAndErrors(bookingForm) {
    bookingForm.reset();

    const errorFields = bookingForm.querySelectorAll(".error-message");
    errorFields.forEach((field) => {
        field.textContent = "";
    });

    document.getElementById('pricePerPerson').textContent = "0.00";
    document.getElementById('totalAmount').textContent = "0.00";
}

function closeModal(modal, bookingForm) {
    let body = document.body;
    if (bookingForm) {
        clearFormAndErrors(bookingForm);
    }
    modal.classList.add('hidden');
    body.style.overflow = '';
    body.style.position = '';
    body.style.width = '';
}


function bookNow(vegPrice, nonVegPrice) {
    const bookingModal = document.getElementById('bookingModal');
    const bookNowBtn = document.getElementById('bookNowBtn');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const bookingForm = document.getElementById('bookingForm');


    closeModalBtn.addEventListener('click', function () {
        closeModal(bookingModal, bookingForm);
    });

    const totalPeopleInput = document.getElementById('total_people');
    const mealTypeSelect = document.getElementById('meal_type');
    const priceDisplay = document.getElementById('pricePerPerson');
    const totalAmountDisplay = document.getElementById('totalAmount');

    function updateTotalAmount() {
        const totalPeople = totalPeopleInput.value;
        const mealType = mealTypeSelect.value;
        let pricePerPerson = 0;

        if (mealType === 'Vegetarian') {
            pricePerPerson = Number(vegPrice);
        } else if (mealType === 'Non-Vegetarian') {
            pricePerPerson = Number(nonVegPrice);
        }

        priceDisplay.textContent = pricePerPerson.toFixed(2);
        const totalAmount = totalPeople * pricePerPerson;
        totalAmountDisplay.textContent = totalAmount.toFixed(2);
    }

    totalPeopleInput.addEventListener('input', updateTotalAmount);
    mealTypeSelect.addEventListener('change', updateTotalAmount);

    updateTotalAmount();

    bookingForm.addEventListener('submit', async function (event) {
        event.preventDefault();

        // Clear previous errors
        document.getElementById("total_people_error").innerHTML = "";
        document.getElementById("booked_for_error").innerHTML = "";
        document.getElementById("meal_type_error").innerHTML = "";

        // Show loading state
        const submitButton = this.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        submitButton.innerHTML = 'Booking...';

        try {
            const csrfToken = this.querySelector("[name=csrfmiddlewaretoken]").value;
            const formData = {
                total_people: this.total_people.value,
                meal_type: this.meal_type.value,
                venue: this.venue.value,
                booked_for: this.booked_for.value,
                user: this.user.value
            };

            const response = await fetch(this.action, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'x-requested-with': 'XMLHttpRequest',
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();
            if (!response.ok) {
                if (data.redirect_url) {
                    window.location.href = data.redirect_url;
                } else if (data.errors) {
                    for (let field in data.errors) {
                        let errorMessage = data.errors[field];
                        document.getElementById(field + "_error").innerHTML = errorMessage;
                    }
                } else {
                    alert(data.errors || 'Booking failed');
                }
            } else {
                closeModal(bookingModal, bookingForm);
            }

            if (response.ok) {
                const paymentModal = document.getElementById('paymentModal');
                openModal(paymentModal);
                pay(data.booking_id);
            }
        } catch (error) {
            console.error('Booking error:', error);
            alert(`Error: ${error.message}`);
        } finally {
            submitButton.disabled = false;
            submitButton.innerHTML = 'Confirm Booking';
        }
    });
}


function pay(bookingId) {
    const paymentModal = document.querySelector("#paymentModal");
    document.querySelectorAll('.payment-option').forEach(option => {
        option.addEventListener('click', async function () {
            const paymentMethod = this.textContent.trim();

            if (paymentMethod === "Khalti") {
                const response = await fetch(`http://localhost:8000/venue/pay-booking/${bookingId}/`);
                const jsonData = await response.json();
                const data = jsonData.data;

                if (jsonData.success && data?.payment_url) {
                    window.location.href = data.payment_url;
                }

            }
        });
    });
}

async function cancelBooking(bookingId) {
    const response = await fetch(`/venue/cancel-booking?id=${bookingId}`, {
        method: 'GET'
    });
    const data = await response.json();

    if (data.success) {
        alert('Booking has been successfully cancelled!');
        window.location.reload();
    } else {
        alert('Failed to cancel booking: ' + (data.message || 'Unknown error.'));
    }
}
