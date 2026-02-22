function randomWord() {
    let things = ["admiring", "adoring", "affectionate", "agitated", "amazing",
        "angry", "awesome", "beautiful", "blissful", "bold", "boring",
        "brave", "busy", "charming", "clever", "cool", "compassionate", "competent",
        "confident", "dazzling", "determined", "sweet", "sad", "silly",
        "relaxed", "romantic", "sad", "serene", "sharp", "quirky", "scared",
        "sleepy", "stoic", "strange", "suspicious", "sweet", "tender", "thirsty",
        "trusting", "unruffled", "upbeat", "vibrant", "vigilant", "vigorous",
        "wizardly", "wonderful", "youthful", "zealous", "zen"];

    let names = ["austin", "borg", "bohr", "wozniak", "bose", "wu", "wing", "wilson",
        "boyd", "guss", "jobs", "hawking", "hertz", "ford", "solomon", "spence",
        "turing", "torvalds", "morse", "ford", "penicillin", "lovelace", "davinci",
        "darwin", "buck", "brown", "benz", "boss", "allen", "gates", "bose",
        "edison", "einstein", "feynman", "ferman", "franklin", "lincoln", "jefferson",
        "mandela", "gandhi", "curie", "newton", "tesla", "faraday", "bell",
        "aristotle", "hubble", "nobel", "pascal", "washington", "galileo"];

    let n1 = things[Math.floor(Math.random() * things.length)];
    let n2 = names[Math.floor(Math.random() * names.length)];
    return `${n1}_${n2}`;
}

function copyClipboard(element) {
    element.select();
    element.setSelectionRange(0, 99999);
    document.execCommand("copy");
}

function isValidURL(str) {
    let pattern = new RegExp('^(https?:\\/\\/)?' + // protocol
        '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|' + // domain name
        '((\\d{1,3}\\.){3}\\d{1,3}))' + // OR ip (v4) address
        '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*' + // port and path
        '(\\?[;&a-z\\d%_.~+=-]*)?' + // query string
        '(\\#[-a-z\\d_]*)?$', 'i'); // fragment locator
    return !!pattern.test(str);
}

function requestGeoPosition() {
    // console.log('Requesting GeoLocation data from the browser...');
    if (navigator.geolocation) {
        navigator.geolocation.watchPosition(showGeoPosition, logGeoLocationError,
            {maximumAge: 600000, timeout: 8000, enableHighAccuracy: true});
    } else {
        console.log('Browser does not support Geo Location');
    }
}

function logGeoLocationError(error) {
    switch (error.code) {
        case error.PERMISSION_DENIED:
            console.log('User denied the request for GeoLocation.');
            break;
        case error.POSITION_UNAVAILABLE:
            console.log('Location information is unavailable.');
            break;
        case error.TIMEOUT:
            console.log('The request to get user location timed out.');
            break;
        default:
            console.log('An unknown error occurred.');
            break;
    }
}

function showGeoPosition(position) {
    let loc = `${position.coords.latitude},${position.coords.longitude},${position.coords.accuracy},${position.timestamp}`;
    console.log(`Tracking geolocation for ${loc}`);
    $('[name="geolocation"]').val(loc);
}


function preserveAnchorTagOnForm() {
    $('#fm1').submit(() => {
        let location = self.document.location;

        let action = $('#fm1').attr('action');
        if (action === undefined) {
            action = location.href;
        } else {
            action += location.search + encodeURIComponent(location.hash);
        }
        $('#fm1').attr('action', action);

    });
}

function preventFormResubmission() {
    $('form').submit(() => {
        $(':submit').attr('disabled', true);
        let altText = $(':submit').attr('data-processing-text');
        if (altText) {
            $(':submit').attr('value', altText);
        }
        return true;
    });
}

function writeToSessionStorage(value) {
    if (typeof (Storage) !== "undefined") {
        window.sessionStorage.removeItem("sessionStorage");
        window.sessionStorage.setItem('sessionStorage', value);
        console.log(`Stored ${value} in session storage`);
    } else {
        console.log("Browser does not support session storage for write-ops");
    }
}

function readFromSessionStorage() {
    if (typeof (Storage) !== "undefined") {
        let sessionStorage = window.sessionStorage.getItem("sessionStorage");
        console.log(`Read ${sessionStorage} in session storage`);
        window.localStorage.removeItem("sessionStorage");
        return sessionStorage;
    } else {
        console.log("Browser does not support session storage for read-ops");
    }
    return null;
}

function resourceLoadedSuccessfully() {
    $(document).ready(() => {
        if (trackGeoLocation) {
            requestGeoPosition();
        }

        if ($(':focus').length === 0) {
            $('input:visible:enabled:first').focus();
        }

        preserveAnchorTagOnForm();
        preventFormResubmission();
        $('#fm1 input[name="username"],[name="password"]').trigger('input');
        $('#fm1 input[name="username"]').focus();

        $('.reveal-password').click(ev => {
            if ($('.pwd').attr('type') !== 'text') {
                $('.pwd').attr('type', 'text');
                $(".reveal-password-icon").removeClass("mdi mdi-eye").addClass("mdi mdi-eye-off");
            } else {
                $('.pwd').attr('type', 'password');
                $(".reveal-password-icon").removeClass("mdi mdi-eye-off").addClass("mdi mdi-eye");
            }
            ev.preventDefault();
        });
        // console.log(`JQuery Ready: ${typeof (jqueryReady)}`);
        if (typeof (jqueryReady) == 'function') {
            jqueryReady();
        }
    });

}
/**
 * ISIC CAS Theme Loader
 * Injecte le CSS ISIC et modifie le DOM pour le branding ISIC
 */
(function() {
    'use strict';

    // 1. Injecter le CSS ISIC
    var link = document.createElement('link');
    link.rel = 'stylesheet';
    link.type = 'text/css';
    link.href = '/cas/themes/isic/css/isic-cas.css';
    document.head.appendChild(link);

    // 2. Attendre que le DOM soit pret
    function applyISICBranding() {
        // Remplacer le logo CAS par le logo ISIC
        var casLogo = document.getElementById('cas-logo');
        if (casLogo) {
            casLogo.src = '/cas/images/isic-logo.png';
            casLogo.title = 'ISIC';
            casLogo.style.maxWidth = '120px';
            casLogo.style.filter = 'none';
        }

        // Changer le titre dans la barre de navigation
        var drawerTitle = document.querySelector('.mdc-drawer__title');
        if (drawerTitle) {
            drawerTitle.textContent = 'ISIC';
        }
        var drawerSubtitle = document.querySelector('.mdc-drawer__subtitle');
        if (drawerSubtitle) {
            drawerSubtitle.textContent = 'Espace Num\u00e9rique';
        }

        // Changer le titre de la page
        document.title = 'ISIC - Authentification';

        // Ajouter le header ISIC avant le formulaire de login
        var loginCard = document.querySelector('.mdc-card-content');
        if (loginCard && !document.getElementById('isic-header')) {
            var header = document.createElement('div');
            header.id = 'isic-header';
            header.className = 'isic-login-header';
            header.innerHTML = '<img src="/cas/images/isic-logo.png" alt="ISIC" class="isic-logo"/>'
                + '<h1 class="isic-title">Espace Num\u00e9rique ISIC</h1>'
                + '<p class="isic-subtitle">Institut Sup\u00e9rieur de l\u2019Information et de la Communication</p>';
            loginCard.parentNode.insertBefore(header, loginCard);
        }

        // Ajouter le footer ISIC
        var mainContent = document.getElementById('main-content');
        if (mainContent && !document.getElementById('isic-footer')) {
            var footer = document.createElement('div');
            footer.id = 'isic-footer';
            footer.className = 'isic-login-footer';
            footer.innerHTML = '<p>Plateforme de gestion acad\u00e9mique <strong>ISIC</strong></p>'
                + '<div class="isic-footer-links">'
                + '<a href="https://isic.ac.ma" target="_blank">isic.ac.ma</a>'
                + ' <span>|</span> '
                + '<a href="https://isic.ac.ma/contact" target="_blank">Contact</a>'
                + ' <span>|</span> '
                + '<a href="https://isic.ac.ma/faq" target="_blank">Aide</a>'
                + '</div>';
            mainContent.appendChild(footer);
        }

        // Traduire les labels en francais
        var instructions = document.querySelector('h3.text-center span');
        if (instructions) {
            instructions.textContent = 'Entrez votre identifiant et votre mot de passe.';
        }

        // Traduire le bouton de soumission
        var submitBtn = document.querySelector('button[type="submit"] .mdc-button__label, input[type="submit"]');
        if (submitBtn) {
            submitBtn.textContent = 'SE CONNECTER';
        }

        // Traduire les labels des champs
        var usernameLabel = document.querySelector('#usernameSection .mdc-floating-label');
        if (usernameLabel) {
            usernameLabel.textContent = 'Identifiant :';
        }
        var passwordLabel = document.querySelector('#passwordSection .mdc-floating-label');
        if (passwordLabel) {
            passwordLabel.textContent = 'Mot de passe :';
        }

        // Message de securite
        var securityNotice = document.querySelector('#content p:last-of-type');
        if (securityNotice && securityNotice.textContent.indexOf('security') !== -1) {
            securityNotice.innerHTML = 'Pour des raisons de s\u00e9curit\u00e9, veuillez vous <a href="logout">d\u00e9connecter</a> et fermer votre navigateur lorsque vous avez fini d\u2019acc\u00e9der aux services authentifi\u00e9s.';
        }

        // Traduire "Mot de passe oublie"
        var forgotPwd = document.querySelector('a[href*="pswdreset"]');
        if (forgotPwd) {
            forgotPwd.textContent = 'Mot de passe oubli\u00e9 ?';
        }
    }

    // Appliquer au chargement
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyISICBranding);
    } else {
        applyISICBranding();
    }

    // Re-appliquer apres un court delai (certains elements CAS sont charges en async)
    setTimeout(applyISICBranding, 500);
})();
