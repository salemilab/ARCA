function validate_submit(field) {
    sub_btn = document.getElementById('search_submit');
    warn = document.getElementById('warn_msg');
    virus_menu = document.getElementById('f_viruses');
    reg_menu = document.getElementById('f_region');
    country_menu = document.getElementById('f_country');

    if (field == "f_region") {
	update_countries(reg_menu, country_menu);
    }

    good = ( (virus_menu.value != "") && ((reg_menu.value != "") || (country_menu.value != "")) )

    if (good) {
	sub_btn.removeAttribute('disabled');
	warn.style.display = 'none';
    } else {
	sub_btn.setAttribute('disabled', 'Y');
	warn.style.display = 'block';
    }
}

function update_countries(reg_menu, country_menu) {
    const country_map = [ ["1", "3", "4"],
			  ["2", "6", "7", "8", "9", "10", "11", "12", "13"],
			  ["3", "15", "16", "17", "18", "19"],
			  ["4", "21", "22", "23", "24", "64"],
			  ["5", "26", "27", "28"],
			  ["6", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50", "51", "52", "53", "54", "55", "56", "57", "65"],
			  ["7", "3", "4", "6", "7", "8", "9", "10", "11", "12", "13", "15", "16", "17", "18", "19", "21", "22", "23", "24", "64", "26", "27", "28", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50", "51", "52", "53", "54", "55", "56", "57", "65"] ];

    reg_selected = [];
    reg_options = reg_menu.options;
    for (var i=0; i < reg_options.length; i++) {
	opt = reg_options[i]
	if (opt.selected) {
	    reg_selected.push(opt.value);
	}
    }

    to_select = []
    for (row of country_map) {
	if (reg_selected.includes(row[0])) {
	    for (var j = 1; j < row.length; j ++) {
		to_select.push(row[j]);
	    }
	}
    }

    coptions = country_menu.options;
    for (var x = 0; x < coptions.length; x++) {
	opt = coptions[x];
	if (to_select.includes(opt.value)) {
	    opt.selected = true;
	} else {
	    opt.selected = false;
	}
    }
}

// Code for checkboxes

function toggle_visible(chk, elt, idx) {
    el = document.getElementById(elt);
    if (chk) {
	el.style.display = 'block';
	el.style.width = "100%";
	fname = "draw_plot_" + idx + "()"
	//	eval(fname);
	f = window.Function(fname);
	f();
    } else {
	el.style.display = 'none';
    }
}


function validate_submit_map(field) {
    sub_btn = document.getElementById('map_submit');
    virus_menu = document.getElementById('f_virus');
    year_menu = document.getElementById('f_year');

    good = ( (virus_menu.value != "0") && (year_menu.value != "0") )

    if (good) {
	sub_btn.removeAttribute('disabled');
    } else {
	sub_btn.setAttribute('disabled', 'Y');
    }
}

