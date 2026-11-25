extends SceneTree
# Black-box acceptance probe for the Godot rocket game. Uses only: the project's main scene, a Node3D named by ROCKET_NODE (default "Rocket") (the
# challenge says it is the player vehicle) and injected keyboard events (Enter, Space, R). Runs deterministic 60 Hz physics
# frames (start Godot with --fixed-fps 60). Mode "probe" (headless) prints one PROBE json line; mode "shots" (windowed) saves PNGs.
var scene: Node
var rocket: Node3D
var y0 := 0.0
var out := {}
var mode := "probe"
var shot_dir := ""

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() > 0: mode = args[0]
	if args.size() > 1: shot_dir = args[1]
	_run.call_deferred()

func key(code: Key, pressed: bool) -> void:
	var e := InputEventKey.new()
	e.keycode = code; e.physical_keycode = code; e.pressed = pressed
	Input.parse_input_event(e)
	Input.flush_buffered_events()

func frames(n: int) -> void:
	for i in n:
		await physics_frame

func alt() -> float:
	return rocket.global_position.y - y0

func fresh() -> bool:
	if scene != null:
		scene.queue_free()
		await process_frame
		await process_frame
	var path: String = ProjectSettings.get_setting("application/run/main_scene", "")
	var packed := load(path) as PackedScene
	if packed == null:
		return false
	scene = packed.instantiate()
	root.add_child(scene)
	current_scene = scene
	await frames(4)
	rocket = scene.find_child(OS.get_environment("ROCKET_NODE") if OS.get_environment("ROCKET_NODE") != "" else "Rocket", true, false) as Node3D
	if rocket == null:
		return false
	y0 = rocket.global_position.y
	return true

func rec(name: String, ok: bool, detail: Variant = "") -> void:
	out[name] = {"ok": ok, "detail": detail}

func shot(name: String) -> void:
	await process_frame
	await process_frame
	var img := root.get_viewport().get_texture().get_image()
	img.save_png(shot_dir.path_join(name + ".png"))

func pulse_run(burn: float, coast: float) -> Dictionary:
	# Enter, wait out the countdown, then pulse Space. Returns max altitude and whether it froze after reaching 150.
	await fresh()
	key(KEY_ENTER, true); key(KEY_ENTER, false)
	await frames(195)
	var maxalt := alt()
	var t := 0
	var won_alt := -1.0
	while t < 31 * 60:
		key(KEY_SPACE, true)
		var nb := int(round(burn * 60))
		for i in nb:
			await physics_frame; t += 1
			maxalt = maxf(maxalt, alt())
			if alt() >= 149.5 and won_alt < 0: won_alt = alt()
		key(KEY_SPACE, false)
		var nc := int(round(coast * 60))
		for i in nc:
			await physics_frame; t += 1
			maxalt = maxf(maxalt, alt())
			if alt() >= 149.5 and won_alt < 0: won_alt = alt()
		if won_alt > 0: break
	var after := -1.0
	if won_alt > 0:
		await frames(120)
		after = alt()
	return {"max": maxalt, "won_alt": won_alt, "alt_2s_after": after, "t_frames": t}

func _run() -> void:
	create_timer(4000.0, true, false, true).timeout.connect(func():
		print("PROBE_WATCHDOG"); quit(0))
	if not await fresh():
		print("PROBE " + JSON.stringify({"fatal": "main scene or the rocket node not found (set ROCKET_NODE to its node name)"})); quit(0); return
	if mode == "shots":
		await frames(30); await shot("1-ready")
		key(KEY_ENTER, true); key(KEY_ENTER, false); await frames(60); await shot("2-countdown")
		key(KEY_SPACE, true); await frames(190 - 60 + 60); await shot("3-flight")
		await frames(120); await shot("4-flight-later")
		key(KEY_SPACE, false); await frames(60); await shot("5-coast")
		key(KEY_SPACE, true); await frames(600); await shot("6-result-overheat?")
		key(KEY_SPACE, false); key(KEY_R, true); key(KEY_R, false); await frames(30); await shot("7-after-reset")
		quit(0); return
	# T1: Space alone must not start; Enter starts a 3 s countdown during which the rocket stays on its stand
	key(KEY_SPACE, true); await frames(150)
	rec("space_alone_does_not_start", absf(alt()) < 0.01, alt())
	key(KEY_SPACE, false)
	await fresh()
	key(KEY_ENTER, true); key(KEY_ENTER, false); key(KEY_SPACE, true)
	var lift := -1
	for i in 400:
		await physics_frame
		if alt() > 0.05 and lift < 0: lift = i + 1
	rec("countdown_about_3s_then_liftoff_with_space_held", lift >= 170 and lift <= 205, {"liftoff_frame_after_enter": lift})
	# T3: continuous thrust must not win (overheat first)
	await fresh()
	key(KEY_ENTER, true); key(KEY_ENTER, false); key(KEY_SPACE, true)
	var maxc := 0.0
	for i in 36 * 60:
		await physics_frame; maxc = maxf(maxc, alt())
	key(KEY_SPACE, false)
	rec("continuous_thrust_does_not_win", maxc > 5.0 and maxc < 149.5, {"max_altitude": maxc})
	# T4: some pulse/coast policy wins (black-box grid; failing to find one is evidence, not proof)
	var wins := []
	var best := 0.0
	for burn in [1.0, 1.5, 2.0, 2.5, 3.0]:
		for coast in [0.5, 1.0, 1.5, 2.0, 2.5]:
			var r: Dictionary = await pulse_run(burn, coast)
			best = maxf(best, r["max"])
			if r["won_alt"] > 0: wins.append({"burn": burn, "coast": coast, "alt_2s_after": r["alt_2s_after"]})
	rec("some_pulse_policy_wins", wins.size() > 0, {"winning": wins.slice(0, 5), "n_winning_of_25": wins.size(), "best_max_altitude": best})
	if wins.size() > 0:
		rec("round_stops_after_win", absf(wins[0]["alt_2s_after"] - 150.0) < 6.0 or wins[0]["alt_2s_after"] >= 149.0, wins[0])
	# T5: R resets in flight; then a new round starts from the stand (countdown again)
	await fresh()
	key(KEY_ENTER, true); key(KEY_ENTER, false); key(KEY_SPACE, true); await frames(300)
	var mid := alt()
	key(KEY_R, true); key(KEY_R, false); key(KEY_SPACE, false); await frames(3)
	var back := alt()
	rec("reset_in_flight_returns_to_stand", mid > 1.0 and absf(back) < 0.05, {"before": mid, "after": back})
	key(KEY_ENTER, true); key(KEY_ENTER, false); key(KEY_SPACE, true)
	var lift2 := -1
	for i in 400:
		await physics_frame
		if alt() > 0.05 and lift2 < 0: lift2 = i + 1
	key(KEY_SPACE, false)
	rec("second_round_after_reset_counts_down_again", lift2 >= 170 and lift2 <= 205, {"liftoff_frame": lift2})
	# T6: reset during countdown leaves no stale timer that launches later
	await fresh()
	key(KEY_ENTER, true); key(KEY_ENTER, false); await frames(60)
	key(KEY_R, true); key(KEY_R, false); key(KEY_SPACE, true); await frames(420)
	rec("reset_in_countdown_no_stale_launch", absf(alt()) < 0.05, alt())
	key(KEY_SPACE, false)
	# T7: ground impact after a short burn is terminal; held Space does not restart
	await fresh()
	key(KEY_ENTER, true); key(KEY_ENTER, false); await frames(195)
	key(KEY_SPACE, true); await frames(36); key(KEY_SPACE, false)
	var peak := 0.0
	for i in 600:
		await physics_frame; peak = maxf(peak, alt())
	var landed := alt()
	key(KEY_SPACE, true); await frames(120)
	rec("ground_impact_is_terminal_and_space_does_not_restart", peak > 0.5 and absf(landed) < 0.05 and absf(alt()) < 0.05, {"peak": peak, "landed": landed, "after_space": alt()})
	key(KEY_SPACE, false)
	# T8: sitting on the pad after the countdown must not crash immediately; thrust still lifts after 5 s
	await fresh()
	key(KEY_ENTER, true); key(KEY_ENTER, false); await frames(195 + 300)
	key(KEY_SPACE, true); await frames(240)
	rec("pad_sit_5s_then_thrust_lifts_within_4s", alt() > 1.0, alt())
	key(KEY_SPACE, false)
	# T9: 30 s without thrust ends the round (time limit); Space afterwards does nothing
	await fresh()
	key(KEY_ENTER, true); key(KEY_ENTER, false); await frames(195 + 31 * 60)
	key(KEY_SPACE, true); await frames(90)
	rec("time_limit_is_terminal", absf(alt()) < 0.05, alt())
	key(KEY_SPACE, false)
	var ok_n := 0
	for k in out: if out[k]["ok"]: ok_n += 1
	out["_summary"] = {"passed": ok_n, "total": out.size()}
	print("PROBE " + JSON.stringify(out))
	quit(0)
