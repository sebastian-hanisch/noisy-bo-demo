"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Permalink-Einrasten."""

import nbo_constants as C
import nbo_evaluation as ev
import nbo_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_control_bounds_and_choices():
    for preset in C.PRESETS.values():
        assert C.N_MIN <= preset["n"] <= C.N_MAX and preset["noise"] in C.BRANIN_NOISES and preset["trucks"] in C.TRUCK_CHOICES
        assert preset["rule"] in C.RULES and preset["repeats"] in C.REPEAT_CHOICES and isinstance(preset["crn"], bool) and 0 <= preset["seed"] <= C.SEED_MAX


def test_default_preset_equals_the_default_settings_and_choice():
    p = C.PRESETS["Standardfall (Voreinstellung)"]
    assert ev.Settings(n=p["n"], noise=p["noise"], trucks=p["trucks"], seed=p["seed"]) == ev.Settings()
    assert ev.Choice(rule=p["rule"], repeats=p["repeats"], crn=p["crn"]) == ev.BASE


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) <= set(P.SETTING_SPECS)


def test_permalink_values_snap_to_allowed_choices():
    assert P.snap_to_choice(7.0, C.BRANIN_NOISES, 5.0) == 5.0
    assert P.snap_to_choice(100.0, C.BRANIN_NOISES, 5.0) == 20.0
    assert P.snap_to_choice("unsinn", C.RULES, "obs") == "obs"
    assert P.snap_to_choice(4, C.REPEAT_CHOICES, 1) in (3, 5)
    assert P._to_bool("true") is True and P._to_bool("0") is False
