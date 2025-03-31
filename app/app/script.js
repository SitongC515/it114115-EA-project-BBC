const moreBtn = document.getElementById("mani-nav-more");
const moreNav = document.getElementById("more-nav");
const crossIcon = document.getElementById("cross-icon");

//Configure weather DPOPDOWN is open or not
let extraMenuOpen = false;

moreBtn.addEventListener("click", e => {
    extraMenuOpen = !extraMenuOpen;

    if(extraMenuOpen){
        moreBtn.getElementsByClassName("nav-line")[0].computedStyleMap.display = "block";
        moreNav.style.display = "flex";
    }else{
        moreBtn.getElementsByClassName("nav-line")[0].style.display = "none";
        moreNav.style.display = "none";
    }
});

crossIcon.addEventListener("click", e => {
    extraMenuOpen = false;
    moreBtn.getElementsByClassName("nav-line")[0].style.display = "none";
    moreNav.style.display = "none";
});