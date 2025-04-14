const moreBtn = document.getElementById("main-nav-more");
const moreNav = document.getElementById("more-nav");
const crossIcon = document.getElementById("cross-icon");

// Configure whether the dropdown is open or not
let extraMenuOpen = false;

moreBtn.addEventListener("click", e => {
    extraMenuOpen = !extraMenuOpen;

    if (extraMenuOpen) {
        moreNav.style.display = "flex"; // Show dropdown menu
        moreBtn.querySelector(".nav-line").style.display = "block"; // Show active line
    } else {
        moreNav.style.display = "none"; // Hide dropdown menu
        moreBtn.querySelector(".nav-line").style.display = "none"; // Hide active line
    }
});

crossIcon.addEventListener("click", e => {
    extraMenuOpen = false;
    moreNav.style.display = "none"; // Hide dropdown menu
    moreBtn.querySelector(".nav-line").style.display = "none"; // Hide active line
});