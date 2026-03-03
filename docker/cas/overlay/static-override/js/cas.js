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
 * Restructure le DOM CAS en colonne unique centree,
 * charge Inter, supprime le footer Apereo, ajoute password toggle.
 */
(function() {
    'use strict';

    // 0. Force light color-scheme to prevent browser dark mode overrides
    document.documentElement.style.colorScheme = 'light only';
    if (document.head) {
        var metaCS = document.createElement('meta');
        metaCS.name = 'color-scheme';
        metaCS.content = 'light only';
        document.head.insertBefore(metaCS, document.head.firstChild);
    }

    // 1. Charger la police Inter depuis Google Fonts
    var preconnect = document.createElement('link');
    preconnect.rel = 'preconnect';
    preconnect.href = 'https://fonts.googleapis.com';
    document.head.insertBefore(preconnect, document.head.firstChild);
    var preconnectGstatic = document.createElement('link');
    preconnectGstatic.rel = 'preconnect';
    preconnectGstatic.href = 'https://fonts.gstatic.com';
    preconnectGstatic.crossOrigin = 'anonymous';
    document.head.insertBefore(preconnectGstatic, document.head.firstChild);
    var fontLink = document.createElement('link');
    fontLink.rel = 'stylesheet';
    fontLink.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap';
    document.head.appendChild(fontLink);

    // 2. Supprimer le footer Apereo
    function removeApereoFooter() {
        document.querySelectorAll('footer, .cas-footer, #cas-footer, [class*="cas-footer"]').forEach(function(el) {
            if (el.id === 'isic-footer') return;
            el.style.display = 'none';
            el.remove();
        });
    }

    function observeFooterRemoval() {
        if (typeof MutationObserver === 'undefined') return;
        var observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType !== 1) return;
                    if (node.tagName === 'FOOTER' ||
                        (node.id && node.id.indexOf('footer') !== -1 && node.id !== 'isic-footer') ||
                        (node.className && typeof node.className === 'string' && node.className.indexOf('cas-footer') !== -1)) {
                        node.remove();
                    }
                });
            });
        });
        observer.observe(document.body || document.documentElement, { childList: true, subtree: true });
    }

    // 3. Password toggle
    function addPasswordToggle() {
        var passwordInput = document.getElementById('password');
        if (!passwordInput || document.getElementById('isic-pwd-toggle')) return;
        var wrapper = passwordInput.parentElement;
        if (!wrapper) return;
        wrapper.classList.add('isic-password-wrapper');
        var toggleBtn = document.createElement('button');
        toggleBtn.type = 'button';
        toggleBtn.id = 'isic-pwd-toggle';
        toggleBtn.className = 'isic-toggle-password';
        toggleBtn.setAttribute('aria-label', 'Afficher/masquer le mot de passe');
        toggleBtn.innerHTML = '\uD83D\uDC41';
        toggleBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                toggleBtn.innerHTML = '\uD83D\uDC41\u200D\uD83D\uDDE8';
            } else {
                passwordInput.type = 'password';
                toggleBtn.innerHTML = '\uD83D\uDC41';
            }
        });
        wrapper.appendChild(toggleBtn);
    }

    // 4. Restructurer le DOM : colonne unique centree
    function restructureDOM() {
        if (document.querySelector('.isic-login-wrapper')) return;

        // Trouver le form CAS et sa section parente
        var form = document.getElementById('fm1');
        if (!form) return;
        var loginSection = form.closest('.login-section') || form.closest('section') || form.parentElement;
        if (!loginSection) return;

        // Trouver le conteneur parent le plus haut dans .main-content
        var mainDiv = document.querySelector('.main-content') || document.getElementById('main-content');
        if (!mainDiv) mainDiv = loginSection.parentElement;

        // Cacher les autres .login-section (panneaux lateraux CAS)
        if (mainDiv) {
            var children = mainDiv.children;
            for (var i = 0; i < children.length; i++) {
                if (children[i] !== loginSection && children[i].tagName === 'SECTION') {
                    children[i].style.display = 'none';
                }
            }
        }

        // Creer le wrapper ISIC
        var wrapper = document.createElement('div');
        wrapper.className = 'isic-login-wrapper';

        // Header ISIC
        var header = document.createElement('div');
        header.id = 'isic-header';
        header.className = 'isic-login-header';
        header.innerHTML = '<img src="/cas/images/isic-logo.png" alt="ISIC" class="isic-logo"/>';
        var titleEl = document.createElement('div');
        titleEl.className = 'isic-title';
        titleEl.textContent = 'l\u2019Espace Num\u00e9rique de l\u2019ISIC Rabat';
        titleEl.style.cssText = 'color:#FFFFFF !important;-webkit-text-fill-color:#FFFFFF !important;opacity:1 !important;display:inline-block !important;visibility:visible !important;font-size:1.5rem;font-weight:700;position:relative;padding-bottom:0.75rem;';
        header.appendChild(titleEl);
        wrapper.appendChild(header);

        // Deplacer la section login dans le wrapper comme carte blanche
        loginSection.classList.add('isic-login-card');
        loginSection.parentElement.insertBefore(wrapper, loginSection);
        wrapper.appendChild(loginSection);

        // Footer ISIC
        var footer = document.createElement('div');
        footer.id = 'isic-footer';
        footer.className = 'isic-login-footer';
        footer.innerHTML = '<p><strong>ISIC</strong> \u00b7 isic.ac.ma</p>'
            + '<div class="isic-footer-links">'
            + '<a href="https://isic.ac.ma" target="_blank" rel="noopener">isic.ac.ma</a>'
            + ' <span>|</span> '
            + '<a href="https://isic.ac.ma/contact" target="_blank" rel="noopener">Contact</a>'
            + ' <span>|</span> '
            + '<a href="https://isic.ac.ma/faq" target="_blank" rel="noopener">Aide</a>'
            + '</div>';
        wrapper.appendChild(footer);
    }

    // 5. Traduire les labels CAS en francais
    function translateLabels() {
        var instructions = document.querySelector('h3.text-center span');
        if (instructions) {
            instructions.textContent = 'Entrez votre identifiant et votre mot de passe.';
        }
        var submitBtn = document.querySelector('button[type="submit"] .mdc-button__label, input[type="submit"]');
        if (submitBtn) {
            submitBtn.textContent = 'SE CONNECTER';
        }
        var usernameLabel = document.querySelector('#usernameSection .mdc-floating-label');
        if (usernameLabel) {
            usernameLabel.textContent = 'Identifiant :';
        }
        var passwordLabel = document.querySelector('#passwordSection .mdc-floating-label');
        if (passwordLabel) {
            passwordLabel.textContent = 'Mot de passe :';
        }
        var securityNotice = document.querySelector('#content p:last-of-type');
        if (securityNotice && securityNotice.textContent.indexOf('security') !== -1) {
            securityNotice.innerHTML = 'Pour des raisons de s\u00e9curit\u00e9, veuillez vous <a href="logout">d\u00e9connecter</a> et fermer votre navigateur lorsque vous avez fini d\u2019acc\u00e9der aux services authentifi\u00e9s.';
        }
        var forgotPwd = document.querySelector('a[href*="pswdreset"]');
        if (forgotPwd) {
            forgotPwd.textContent = 'Mot de passe oubli\u00e9 ?';
        }
    }

    // 6. Appliquer tout le branding
    function applyISICBranding() {
        removeApereoFooter();
        restructureDOM();
        translateLabels();
        addPasswordToggle();
        document.title = 'ISIC \u2014 Authentification';
    }

    // Boot
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            applyISICBranding();
            observeFooterRemoval();
        });
    } else {
        applyISICBranding();
        observeFooterRemoval();
    }

    setTimeout(applyISICBranding, 500);
    setTimeout(removeApereoFooter, 1000);
})();
