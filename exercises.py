"""
exercises.py — Evidence-based exercise knowledge base for PhysioGemma
=====================================================================
Clinical references:
  - NICE NG59 (Low back pain)
  - Cochrane Reviews (Knee OA, Neck pain, Frozen shoulder)
  - ACSM Exercise Guidelines
  - Boonstra 2014 (VAS cutoffs)
"""

EXERCISES = {
    "LBP": {
        "name": "Lower Back Pain",
        "levels": {
            1: {
                "label": "Acute / Severe Pain (VAS 7.5-10)",
                "goal": "Pain relief, gentle mobility",
                "exercises": [
                    {"name": "Pelvic Tilt", "sets": 2, "reps": "10", "type": "mobility",
                     "video": "44D6Xc2Fkek", "instruction": "Lie on back, knees bent. Gently flatten lower back against floor by tightening abs. Hold 5 seconds."},
                    {"name": "Knee-to-Chest Stretch", "sets": 2, "reps": "30s hold each side", "type": "stretching",
                     "video": "yVy4L0CGbyQ", "instruction": "Lie on back. Pull one knee gently toward chest. Hold 30 seconds. Switch sides."},
                    {"name": "Cat-Cow Stretch", "sets": 2, "reps": "8", "type": "mobility",
                     "video": "LIVJZZyZ2qM", "instruction": "On hands and knees. Alternate between arching back up (cat) and letting belly drop (cow)."},
                    {"name": "Child's Pose", "sets": 1, "reps": "60s hold", "type": "stretching",
                     "video": "_ZX_zTOBgp8", "instruction": "Kneel, sit back on heels. Stretch arms forward on floor. Breathe deeply and relax."},
                ],
            },
            2: {
                "label": "Moderate Pain (VAS 5.0-7.4)",
                "goal": "Improve stability, begin gentle strengthening",
                "exercises": [
                    {"name": "Glute Bridge", "sets": 3, "reps": "10", "type": "strengthening",
                     "video": "PhTDzR0TpZs", "instruction": "Lie on back, knees bent. Lift hips up squeezing glutes. Hold 3 seconds at top."},
                    {"name": "Bird Dog", "sets": 2, "reps": "8 each side", "type": "stability",
                     "video": "ufCbCMlJLAs", "instruction": "On hands and knees. Extend opposite arm and leg. Hold 5 seconds. Alternate."},
                    {"name": "Modified Dead Bug", "sets": 2, "reps": "8 each side", "type": "stability",
                     "video": "o4GKiEoYClI", "instruction": "Lie on back, arms up, knees at 90 degrees. Slowly lower opposite arm and leg."},
                    {"name": "Hip Flexor Stretch", "sets": 2, "reps": "30s hold each side", "type": "stretching",
                     "video": "DXuStgWuJV8", "instruction": "Kneel on one knee. Push hips forward gently. You should feel a stretch in front of hip."},
                ],
            },
            3: {
                "label": "Mild Pain (VAS 3.5-4.9)",
                "goal": "Core strengthening, functional movement",
                "exercises": [
                    {"name": "Modified Plank", "sets": 3, "reps": "20s hold", "type": "strengthening",
                     "video": "phYU661J6dw", "instruction": "Forearm plank on knees. Keep body straight from head to knees. Hold steady."},
                    {"name": "Side-Lying Hip Abduction", "sets": 3, "reps": "12 each side", "type": "strengthening",
                     "video": "CP4LjhZ_Wq0", "instruction": "Lie on side. Lift top leg 30 degrees, keeping it straight. Lower slowly."},
                    {"name": "Pallof Press", "sets": 2, "reps": "10 each side", "type": "stability",
                     "video": "lcVTzIaqkPE", "instruction": "Stand sideways to resistance band. Press hands forward, resisting rotation. Hold 3 seconds."},
                    {"name": "Seated Hamstring Stretch", "sets": 2, "reps": "30s hold each side", "type": "stretching",
                     "video": "1rscgJNW27g", "instruction": "Sit on floor, one leg extended. Reach toward toes keeping back straight."},
                ],
            },
            4: {
                "label": "Low Pain (VAS 1.0-3.4)",
                "goal": "Advanced strengthening, return to function",
                "exercises": [
                    {"name": "Full Plank", "sets": 3, "reps": "30s hold", "type": "strengthening",
                     "video": "pvIjsG5Svck", "instruction": "Full forearm plank on toes. Keep body perfectly straight. Engage core throughout."},
                    {"name": "Single-Leg Glute Bridge", "sets": 3, "reps": "10 each side", "type": "strengthening",
                     "video": "TWyLUdg21T8", "instruction": "Lie on back. Extend one leg. Lift hips with single leg. Hold 3 seconds."},
                    {"name": "Walking Lunges", "sets": 3, "reps": "10 each side", "type": "strengthening",
                     "video": "AvBrsGNA7V8", "instruction": "Step forward into lunge. Push back up and step with other leg. Keep torso upright."},
                    {"name": "Side Plank", "sets": 2, "reps": "20s each side", "type": "strengthening",
                     "video": "N_s9em1xTqU", "instruction": "Lie on side, forearm on ground. Lift hips. Keep body in straight line."},
                ],
            },
            5: {
                "label": "Minimal/No Pain (VAS 0-0.9)",
                "goal": "Performance, prevention, return to sport",
                "exercises": [
                    {"name": "Romanian Deadlift", "sets": 3, "reps": "10", "type": "strengthening",
                     "video": "QMe5uQd0WFE", "instruction": "Stand on one leg or both. Hinge at hips, lowering hands toward floor. Keep back flat."},
                    {"name": "Plank with Shoulder Tap", "sets": 3, "reps": "10 each side", "type": "stability",
                     "video": "8rgurWd-PB8", "instruction": "In full plank. Tap opposite shoulder with hand. Minimize hip rotation."},
                    {"name": "Single-Leg Squat", "sets": 3, "reps": "8 each side", "type": "strengthening",
                     "video": "0CodCXxgMk4", "instruction": "Stand on one leg. Lower into partial squat. Keep knee over toes. Push back up."},
                    {"name": "Farmer's Carry", "sets": 3, "reps": "30m walk", "type": "strengthening",
                     "video": "p5MNNosenJc", "instruction": "Hold weights at sides. Walk with tall posture. Engage core throughout."},
                ],
            },
        },
    },
    "KNEE_OA": {
        "name": "Knee Pain / Osteoarthritis",
        "levels": {
            1: {
                "label": "Acute / Severe Pain (VAS 7.5-10)",
                "goal": "Pain relief, maintain range of motion",
                "exercises": [
                    {"name": "Quad Sets", "sets": 2, "reps": "10, hold 5s", "type": "strengthening",
                     "video": "au62CidApd0", "instruction": "Sit with leg straight. Tighten thigh muscle pressing knee flat. Hold 5 seconds."},
                    {"name": "Straight Leg Raise", "sets": 2, "reps": "10 each side", "type": "strengthening",
                     "video": "Ka19yzAlIGY", "instruction": "Lie on back, one leg bent. Lift straight leg to height of bent knee. Lower slowly."},
                    {"name": "Heel Slides", "sets": 2, "reps": "10", "type": "mobility",
                     "video": "m6Iod6_kaDc", "instruction": "Lie on back. Slide heel toward buttocks bending knee. Slide back out slowly."},
                    {"name": "Ankle Pumps", "sets": 2, "reps": "15", "type": "mobility",
                     "video": "KxfFzSOAT7g", "instruction": "Lie or sit with legs extended. Pump ankles up and down to improve circulation."},
                ],
            },
            2: {
                "label": "Moderate Pain (VAS 5.0-7.4)",
                "goal": "Build quad and hip strength",
                "exercises": [
                    {"name": "Mini Squat", "sets": 3, "reps": "10", "type": "strengthening",
                     "video": "wqCvuhfRXRU", "instruction": "Stand with feet shoulder width. Lower into quarter squat. Keep weight on heels."},
                    {"name": "Clamshell", "sets": 3, "reps": "12 each side", "type": "strengthening",
                     "video": "O2KPabIoPPk", "instruction": "Lie on side, knees bent. Keep feet together, open top knee like a clamshell. Lower slowly."},
                    {"name": "Seated Knee Extension", "sets": 3, "reps": "10 each side", "type": "strengthening",
                     "video": "VuJZ6dqMf8M", "instruction": "Sit in chair. Straighten one knee fully. Hold 3 seconds. Lower slowly."},
                    {"name": "Wall Slide", "sets": 2, "reps": "10", "type": "strengthening",
                     "video": "xhbpQ80JiUQ", "instruction": "Lean against wall. Slide down into partial squat. Hold 5 seconds. Slide back up."},
                ],
            },
            3: {
                "label": "Mild Pain (VAS 3.5-4.9)",
                "goal": "Functional strengthening",
                "exercises": [
                    {"name": "Sit-to-Stand", "sets": 3, "reps": "10", "type": "strengthening",
                     "video": "cUz_TSy7_fw", "instruction": "Sit in chair. Stand up without using hands. Sit back down slowly with control."},
                    {"name": "Step-Up (Low)", "sets": 3, "reps": "10 each side", "type": "strengthening",
                     "video": "wfhXnLILqdk", "instruction": "Step up onto low step. Push through heel. Step down with control."},
                    {"name": "Calf Raise", "sets": 3, "reps": "12", "type": "strengthening",
                     "video": "nnPGrBLNlaw", "instruction": "Stand on edge of step. Rise up on toes. Lower heels below step level slowly."},
                    {"name": "Terminal Knee Extension", "sets": 3, "reps": "12 each side", "type": "strengthening",
                     "video": "p9tb23xpulw", "instruction": "Loop band behind knee. Start with knee slightly bent. Straighten fully against resistance."},
                ],
            },
            4: {
                "label": "Low Pain (VAS 1.0-3.4)",
                "goal": "Advanced strengthening, balance training",
                "exercises": [
                    {"name": "Full Squat", "sets": 3, "reps": "12", "type": "strengthening",
                     "video": "-5LhNSMBrEs", "instruction": "Full depth bodyweight squat. Keep heels flat, chest up, knees tracking over toes."},
                    {"name": "Lateral Band Walk", "sets": 3, "reps": "10 each direction", "type": "strengthening",
                     "video": "kqeqCHh0SxE", "instruction": "Band around ankles. Side-step maintaining tension. Stay low in slight squat."},
                    {"name": "Step-Up (Full Height)", "sets": 3, "reps": "10 each side", "type": "strengthening",
                     "video": "wfhXnLILqdk", "instruction": "Step up onto standard height step. Full weight on stepping leg. Control descent."},
                    {"name": "Eccentric Step Down", "sets": 3, "reps": "8 each side", "type": "strengthening",
                     "video": "h7v741oKXu8", "instruction": "Stand on step on one leg. Slowly lower other foot to ground. Push back up."},
                ],
            },
            5: {
                "label": "Minimal/No Pain (VAS 0-0.9)",
                "goal": "Sport-specific, agility, prevention",
                "exercises": [
                    {"name": "Single-Leg Squat", "sets": 3, "reps": "8 each side", "type": "strengthening",
                     "video": "0CodCXxgMk4", "instruction": "Stand on one leg. Lower into controlled squat. Keep knee aligned. Push back up."},
                    {"name": "Walking Lunges", "sets": 3, "reps": "10 each side", "type": "strengthening",
                     "video": "AvBrsGNA7V8", "instruction": "Step forward into deep lunge. Push off and step through. Maintain upright posture."},
                    {"name": "Lateral Band Walk", "sets": 3, "reps": "12 each direction", "type": "strengthening",
                     "video": "kqeqCHh0SxE", "instruction": "Band above knees. Wider stance, deeper squat. Side-step with purpose."},
                    {"name": "Box Jump (Low)", "sets": 3, "reps": "6", "type": "plyometric",
                     "video": "hxldG9FX4j8", "instruction": "Stand in front of low box. Jump up landing softly with bent knees. Step down."},
                ],
            },
        },
    },
    "NECK": {
        "name": "Neck Pain / Stiff Neck",
        "levels": {
            1: {
                "label": "Acute / Severe Pain (VAS 7.5-10)",
                "goal": "Pain relief, gentle range of motion",
                "exercises": [
                    {"name": "Chin Tuck", "sets": 2, "reps": "10, hold 5s", "type": "mobility",
                     "video": "7rnlAVhAK-8", "instruction": "Sit tall. Draw chin straight back making a double chin. Hold 5 seconds. Relax."},
                    {"name": "Cervical Rotation", "sets": 2, "reps": "8 each side", "type": "mobility",
                     "video": "PruXF-NE2zI", "instruction": "Sit tall. Slowly turn head to one side. Hold 5 seconds. Return and repeat other side."},
                    {"name": "Upper Trapezius Stretch", "sets": 2, "reps": "30s each side", "type": "stretching",
                     "video": "-r0eoFS7_5Q", "instruction": "Tilt head to one side. Gently press with hand. Feel stretch along neck. Hold 30 seconds."},
                    {"name": "Shoulder Rolls", "sets": 2, "reps": "10 each direction", "type": "mobility",
                     "video": "XbzY45Z5DE8", "instruction": "Roll shoulders forward in circles 10 times. Then backward 10 times. Keep relaxed."},
                ],
            },
            2: {
                "label": "Moderate Pain (VAS 5.0-7.4)",
                "goal": "Isometric strengthening, posture correction",
                "exercises": [
                    {"name": "Cervical Isometric Flexion", "sets": 2, "reps": "8, hold 5s", "type": "strengthening",
                     "video": "4rK-m6GvNCk", "instruction": "Place hand on forehead. Push head forward against hand. Don't let head move. Hold 5 seconds."},
                    {"name": "Cervical Isometric Extension", "sets": 2, "reps": "8, hold 5s", "type": "strengthening",
                     "video": "iCiOE7pKVRk", "instruction": "Place hand on back of head. Push head backward against hand. Hold 5 seconds."},
                    {"name": "Scapular Retraction", "sets": 3, "reps": "10", "type": "strengthening",
                     "video": "hJffqKmfnfA", "instruction": "Squeeze shoulder blades together. Hold 5 seconds. Relax. Keep shoulders down."},
                    {"name": "Levator Scapulae Stretch", "sets": 2, "reps": "30s each side", "type": "stretching",
                     "video": "GSoXPJRnR6E", "instruction": "Turn head 45 degrees. Look down toward armpit. Gently pull head down with hand."},
                ],
            },
            3: {
                "label": "Mild Pain (VAS 3.5-4.9)",
                "goal": "Progressive strengthening, endurance",
                "exercises": [
                    {"name": "Chin Tuck with Extension", "sets": 3, "reps": "10", "type": "strengthening",
                     "video": "oOW1X0AYtF4", "instruction": "Do a chin tuck. Then gently extend neck looking up slightly. Return to neutral."},
                    {"name": "Resistance Band Row", "sets": 3, "reps": "12", "type": "strengthening",
                     "video": "ZIAQvUA_wbs", "instruction": "Hold band in front. Pull elbows back squeezing shoulder blades. Control return."},
                    {"name": "Thoracic Extension over Roll", "sets": 2, "reps": "10", "type": "mobility",
                     "video": "9Y11Kc0E0og", "instruction": "Place foam roller under upper back. Support head. Gently extend over roller."},
                    {"name": "Deep Neck Flexor Endurance", "sets": 3, "reps": "15s hold", "type": "strengthening",
                     "video": "tCiX5NJyw4I", "instruction": "Lie on back. Tuck chin. Lift head just off surface. Hold without straining."},
                ],
            },
            4: {
                "label": "Low Pain (VAS 1.0-3.4)",
                "goal": "Functional strengthening, postural endurance",
                "exercises": [
                    {"name": "Prone Y-T-W", "sets": 3, "reps": "8 each position", "type": "strengthening",
                     "video": "QdGTI4Lshg4", "instruction": "Lie face down. Lift arms into Y, T, then W positions. Squeeze shoulder blades each time."},
                    {"name": "Band Face Pull", "sets": 3, "reps": "12", "type": "strengthening",
                     "video": "2Hn4Ahkzk6E", "instruction": "Pull band toward face at eye level. Separate hands as you pull. Squeeze rear delts."},
                    {"name": "Cervical Side Flexion Isometric", "sets": 3, "reps": "8 each side, 5s hold", "type": "strengthening",
                     "video": "3Owy1hurobA", "instruction": "Place hand on side of head. Push sideways against hand. Don't let head move."},
                    {"name": "Overhead Press (Light)", "sets": 3, "reps": "10", "type": "strengthening",
                     "video": "cLmgQRx4kVM", "instruction": "Light weights overhead. Press up fully. Lower with control. Keep core engaged."},
                ],
            },
            5: {
                "label": "Minimal/No Pain (VAS 0-0.9)",
                "goal": "Performance, prevention",
                "exercises": [
                    {"name": "Loaded Scapular Retraction", "sets": 3, "reps": "12", "type": "strengthening",
                     "video": "4tpl-huz060", "instruction": "Use resistance band or weights. Retract scapulae against load. Hold 3 seconds."},
                    {"name": "Neck Endurance Training", "sets": 3, "reps": "20s hold", "type": "strengthening",
                     "video": "qUZ5QzuoQsw", "instruction": "Isometric holds in all directions with increased duration. Build neck endurance."},
                    {"name": "Prone Y-T-W (Weighted)", "sets": 3, "reps": "8 each", "type": "strengthening",
                     "video": "QdGTI4Lshg4", "instruction": "Same as Y-T-W but holding light dumbbells. Focus on scapular control."},
                    {"name": "Band Face Pull", "sets": 3, "reps": "15", "type": "strengthening",
                     "video": "2Hn4Ahkzk6E", "instruction": "Heavier band. Pull toward face with external rotation. Slow eccentric."},
                ],
            },
        },
    },
    "FROZEN_SHOULDER": {
        "name": "Shoulder Pain / Frozen Shoulder",
        "levels": {
            1: {
                "label": "Acute / Freezing Phase (VAS 7.5-10)",
                "goal": "Pain management, prevent further stiffness",
                "exercises": [
                    {"name": "Pendulum Exercise", "sets": 2, "reps": "10 circles each direction", "type": "mobility",
                     "video": "9-DOa672Hxk", "instruction": "Lean forward, let arm hang. Gently swing in small circles. Clockwise then counter-clockwise."},
                    {"name": "Passive Shoulder Flexion (Wand)", "sets": 2, "reps": "8", "type": "mobility",
                     "video": "oG5I8-rA3mU", "instruction": "Hold wand with both hands. Use good arm to push affected arm up overhead gently."},
                    {"name": "Passive External Rotation (Wand)", "sets": 2, "reps": "8", "type": "mobility",
                     "video": "nBpjy4YOyIA", "instruction": "Hold wand, elbow at side bent 90 degrees. Use good arm to push affected arm outward."},
                    {"name": "Table Slide", "sets": 2, "reps": "10", "type": "mobility",
                     "video": "pgsPQ1_5e0w", "instruction": "Sit at table. Slide affected arm forward on table as far as comfortable. Slide back."},
                ],
            },
            2: {
                "label": "Frozen Phase / Moderate Pain (VAS 5.0-7.4)",
                "goal": "Restore range of motion",
                "exercises": [
                    {"name": "Overhead Pulley", "sets": 2, "reps": "10", "type": "mobility",
                     "video": "r1GBoTNhV_k", "instruction": "Pulley over door. Pull with good arm to lift affected arm overhead. Control lowering."},
                    {"name": "Wall Walk (Finger Climbing)", "sets": 2, "reps": "8", "type": "mobility",
                     "video": "7ggOdiyOuDc", "instruction": "Face wall. Walk fingers up wall as high as comfortable. Hold at top. Walk back down."},
                    {"name": "Cross-Body Stretch", "sets": 2, "reps": "30s hold", "type": "stretching",
                     "video": "qq9IkLFxZtw", "instruction": "Pull affected arm across body with other hand. Feel stretch in back of shoulder."},
                    {"name": "Sleeper Stretch", "sets": 2, "reps": "30s hold", "type": "stretching",
                     "video": "5wy6uUPGbFY", "instruction": "Lie on affected side. Arm at 90 degrees. Gently push hand toward floor with other hand."},
                ],
            },
            3: {
                "label": "Thawing Phase / Mild Pain (VAS 3.5-4.9)",
                "goal": "Active ROM, begin strengthening",
                "exercises": [
                    {"name": "Active Shoulder Flexion", "sets": 3, "reps": "10", "type": "mobility",
                     "video": "k-WNso7_Wjg", "instruction": "Raise arm forward and overhead under your own power. Lower with control."},
                    {"name": "Isometric External Rotation", "sets": 3, "reps": "8, hold 5s", "type": "strengthening",
                     "video": "zZO20ICBETM", "instruction": "Elbow at side, bent 90 degrees. Push hand outward against wall or doorframe. Hold."},
                    {"name": "Isometric Internal Rotation", "sets": 3, "reps": "8, hold 5s", "type": "strengthening",
                     "video": "eSu4eyM7uN4", "instruction": "Elbow at side, bent 90 degrees. Push palm inward against wall or doorframe. Hold."},
                    {"name": "Wall Push-Up", "sets": 3, "reps": "10", "type": "strengthening",
                     "video": "JbOMAwlaVcM", "instruction": "Hands on wall at shoulder height. Bend elbows to lean in. Push back. Keep core tight."},
                ],
            },
            4: {
                "label": "Recovery Phase (VAS 1.0-3.4)",
                "goal": "Progressive resistance, functional ROM",
                "exercises": [
                    {"name": "Resistance Band External Rotation", "sets": 3, "reps": "12", "type": "strengthening",
                     "video": "_UvmPNGtlPM", "instruction": "Elbow at side. Pull band outward rotating forearm away from body. Control return."},
                    {"name": "Resistance Band Internal Rotation", "sets": 3, "reps": "12", "type": "strengthening",
                     "video": "ZXncuZKonas", "instruction": "Elbow at side. Pull band inward rotating forearm across body. Control return."},
                    {"name": "Scaption", "sets": 3, "reps": "10", "type": "strengthening",
                     "video": "RsZdXRWYWYI", "instruction": "Raise arms at 30-degree angle from front. Thumbs up. Lift to shoulder height. Lower slowly."},
                    {"name": "Posterior Capsule Stretch", "sets": 2, "reps": "30s hold", "type": "stretching",
                     "video": "TCDA6qCp1FU", "instruction": "Reach affected arm across body. Use other hand to gently push elbow toward chest."},
                ],
            },
            5: {
                "label": "Full Recovery (VAS 0-0.9)",
                "goal": "Full function, prevention, return to activity",
                "exercises": [
                    {"name": "Full Rotator Cuff Program", "sets": 3, "reps": "12 each direction", "type": "strengthening",
                     "video": "y_qh-ImBBpg", "instruction": "Complete internal, external rotation, scaption, and diagonal patterns with band."},
                    {"name": "Dumbbell Shoulder Press", "sets": 3, "reps": "10", "type": "strengthening",
                     "video": "FghebqCF_o8", "instruction": "Light dumbbells at shoulder level. Press overhead fully. Lower with control."},
                    {"name": "Functional Overhead Reach", "sets": 3, "reps": "10", "type": "strengthening",
                     "video": "J5luTInj_kI", "instruction": "Practice reaching overhead as in daily tasks. Controlled, full range of motion."},
                    {"name": "Prone Y-T-W", "sets": 3, "reps": "8 each position", "type": "strengthening",
                     "video": "QdGTI4Lshg4", "instruction": "Lie face down. Lift arms into Y, T, then W positions to strengthen scapular stabilizers."},
                ],
            },
        },
    },
    "SCIATICA": {
        "name": "Sciatica / Radiculopathy",
        "levels": {
            1: {
                "label": "Acute / Severe (VAS 7.5-10)",
                "goal": "Pain relief, reduce nerve irritation",
                "exercises": [
                    {"name": "Prone Lying", "sets": 3, "reps": "5 min", "type": "mobility",
                     "video": "drbK1JE2bqI", "instruction": "Lie face down on firm surface. Place pillow under hips if needed. Breathe deeply and relax."},
                    {"name": "Prone on Elbows (McKenzie)", "sets": 3, "reps": "30s hold", "type": "mobility",
                     "video": "qkS2PLqSJEI", "instruction": "Lie face down. Prop up on elbows. Keep hips on floor. Hold if pain centralizes (moves toward spine)."},
                    {"name": "Knee-to-Chest (Unaffected Side)", "sets": 2, "reps": "30s hold", "type": "stretching",
                     "video": "yVy4L0CGbyQ", "instruction": "Lie on back. Pull unaffected knee to chest. Keeps pelvis tilted to reduce nerve tension."},
                    {"name": "Sciatic Nerve Glide", "sets": 2, "reps": "10 gentle", "type": "mobility",
                     "video": "kYtkCqvOz4A", "instruction": "Sit on chair. Slowly straighten affected leg while looking up. Bend knee while looking down. Gentle pendulum motion."},
                ],
            },
            2: {
                "label": "Moderate (VAS 5.0-7.4)",
                "goal": "Centralize symptoms, begin stabilization",
                "exercises": [
                    {"name": "Press-Up (McKenzie Extension)", "sets": 3, "reps": "10", "type": "mobility",
                     "video": "qkS2PLqSJEI", "instruction": "Lie face down. Push upper body up with arms, keeping hips on floor. Lower slowly. Stop if pain goes further down leg."},
                    {"name": "Pelvic Tilt", "sets": 3, "reps": "10", "type": "stability",
                     "video": "44D6Xc2Fkek", "instruction": "Lie on back, knees bent. Flatten lower back against floor. Hold 5 seconds."},
                    {"name": "Piriformis Stretch", "sets": 2, "reps": "30s each side", "type": "stretching",
                     "video": "wMaKGghFPis", "instruction": "Lie on back. Cross affected leg over other knee. Pull bottom knee toward chest. Feel stretch deep in buttock."},
                    {"name": "Cat-Cow Stretch", "sets": 2, "reps": "10", "type": "mobility",
                     "video": "LIVJZZyZ2qM", "instruction": "On hands and knees. Alternate arching back up and letting belly drop. Gentle spinal mobility."},
                ],
            },
            3: {
                "label": "Mild (VAS 3.5-4.9)",
                "goal": "Core stabilization, nerve mobility",
                "exercises": [
                    {"name": "Bird Dog", "sets": 3, "reps": "8 each side", "type": "stability",
                     "video": "ufCbCMlJLAs", "instruction": "Hands and knees. Extend opposite arm and leg. Hold 5 seconds. Alternate. Keep spine neutral."},
                    {"name": "Glute Bridge", "sets": 3, "reps": "12", "type": "strengthening",
                     "video": "PhTDzR0TpZs", "instruction": "Lie on back, knees bent. Lift hips squeezing glutes. Hold 3 seconds. Strengthens posterior chain."},
                    {"name": "Sciatic Nerve Floss (Advanced)", "sets": 2, "reps": "12", "type": "mobility",
                     "video": "kYtkCqvOz4A", "instruction": "Sit upright. Straighten leg fully while extending neck back. Bend knee while flexing neck forward. Smooth rhythm."},
                    {"name": "Modified Plank", "sets": 3, "reps": "20s hold", "type": "strengthening",
                     "video": "phYU661J6dw", "instruction": "Forearm plank on knees. Straight line from head to knees. Build core endurance."},
                ],
            },
            4: {
                "label": "Low Pain (VAS 1.0-3.4)",
                "goal": "Functional strengthening, return to activity",
                "exercises": [
                    {"name": "Full Plank", "sets": 3, "reps": "30s", "type": "strengthening",
                     "video": "pvIjsG5Svck", "instruction": "Full forearm plank on toes. Straight body line. Core engaged throughout."},
                    {"name": "Single-Leg Glute Bridge", "sets": 3, "reps": "10 each side", "type": "strengthening",
                     "video": "TWyLUdg21T8", "instruction": "Lie on back. One leg extended. Lift hips with single leg. Strengthens gluteus maximus."},
                    {"name": "Clamshell with Band", "sets": 3, "reps": "15 each side", "type": "strengthening",
                     "video": "O2KPabIoPPk", "instruction": "Lie on side, band above knees. Open top knee keeping feet together. Strengthens hip external rotators."},
                    {"name": "Walking Lunges", "sets": 3, "reps": "10 each side", "type": "strengthening",
                     "video": "AvBrsGNA7V8", "instruction": "Step forward into lunge. Push through and step with other leg. Keep torso upright."},
                ],
            },
            5: {
                "label": "Minimal/No Pain (VAS 0-0.9)",
                "goal": "Prevention, return to sport",
                "exercises": [
                    {"name": "Romanian Deadlift", "sets": 3, "reps": "10", "type": "strengthening",
                     "video": "QMe5uQd0WFE", "instruction": "Hinge at hips, lower hands toward floor. Keep back flat. Strengthens entire posterior chain."},
                    {"name": "Side Plank", "sets": 3, "reps": "25s each side", "type": "strengthening",
                     "video": "N_s9em1xTqU", "instruction": "Side-lying, forearm on ground. Lift hips. Straight body line. Core and hip stability."},
                    {"name": "Single-Leg Squat", "sets": 3, "reps": "8 each side", "type": "strengthening",
                     "video": "0CodCXxgMk4", "instruction": "Stand on one leg. Lower into controlled squat. Keep knee aligned. Advanced stability."},
                    {"name": "Farmer's Carry", "sets": 3, "reps": "30m", "type": "strengthening",
                     "video": "p5MNNosenJc", "instruction": "Hold weights at sides. Walk with tall posture. Builds total core and grip endurance."},
                ],
            },
        },
    },
    "HIP_OA": {
        "name": "Hip Pain / Osteoarthritis",
        "levels": {
            1: {
                "label": "Acute / Severe (VAS 7.5-10)",
                "goal": "Pain relief, maintain range of motion",
                "exercises": [
                    {"name": "Supine Hip Flexion", "sets": 2, "reps": "10 each side", "type": "mobility",
                     "video": "yVy4L0CGbyQ", "instruction": "Lie on back. Slide heel toward buttocks bending hip. Slide back out slowly."},
                    {"name": "Heel Slides", "sets": 2, "reps": "10", "type": "mobility",
                     "video": "m6Iod6_kaDc", "instruction": "Lie on back. Slide heel along surface bending and straightening knee/hip."},
                    {"name": "Ankle Pumps", "sets": 2, "reps": "20", "type": "mobility",
                     "video": "KxfFzSOAT7g", "instruction": "Lie or sit with legs extended. Pump ankles up and down to improve circulation."},
                    {"name": "Quad Sets", "sets": 2, "reps": "10, hold 5s", "type": "strengthening",
                     "video": "au62CidApd0", "instruction": "Sit with leg straight. Tighten thigh muscle pressing knee flat. Hold 5 seconds."},
                ],
            },
            2: {
                "label": "Moderate (VAS 5.0-7.4)",
                "goal": "Hip strengthening, improve mobility",
                "exercises": [
                    {"name": "Glute Bridge", "sets": 3, "reps": "10", "type": "strengthening",
                     "video": "PhTDzR0TpZs", "instruction": "Lie on back, knees bent. Lift hips squeezing glutes. Hold 3 seconds at top."},
                    {"name": "Clamshell", "sets": 3, "reps": "12 each side", "type": "strengthening",
                     "video": "O2KPabIoPPk", "instruction": "Lie on side, knees bent. Open top knee like clamshell. Strengthens hip abductors."},
                    {"name": "Standing Hip Flexion", "sets": 2, "reps": "10 each side", "type": "mobility",
                     "video": "5p2fVhKzXE4", "instruction": "Stand holding chair. Lift knee toward chest. Lower with control. Maintain balance."},
                    {"name": "Hip Flexor Stretch", "sets": 2, "reps": "30s each side", "type": "stretching",
                     "video": "DXuStgWuJV8", "instruction": "Kneel on one knee. Push hips forward. Feel stretch in front of hip."},
                ],
            },
            3: {
                "label": "Mild (VAS 3.5-4.9)",
                "goal": "Functional strengthening",
                "exercises": [
                    {"name": "Mini Squat", "sets": 3, "reps": "12", "type": "strengthening",
                     "video": "wqCvuhfRXRU", "instruction": "Feet shoulder width. Lower into quarter squat. Keep weight on heels."},
                    {"name": "Side-Lying Hip Abduction", "sets": 3, "reps": "12 each side", "type": "strengthening",
                     "video": "CP4LjhZ_Wq0", "instruction": "Lie on side. Lift top leg 30 degrees keeping it straight. Lower slowly."},
                    {"name": "Sit-to-Stand", "sets": 3, "reps": "10", "type": "strengthening",
                     "video": "cUz_TSy7_fw", "instruction": "Sit in chair. Stand up without using hands. Sit back down with control."},
                    {"name": "Standing Hip Extension", "sets": 3, "reps": "10 each side", "type": "strengthening",
                     "video": "5p2fVhKzXE4", "instruction": "Stand holding chair. Extend leg backward. Squeeze glute at top. Lower slowly."},
                ],
            },
            4: {
                "label": "Low Pain (VAS 1.0-3.4)",
                "goal": "Advanced hip strengthening, balance",
                "exercises": [
                    {"name": "Full Squat", "sets": 3, "reps": "12", "type": "strengthening",
                     "video": "-5LhNSMBrEs", "instruction": "Full depth bodyweight squat. Heels flat, chest up, knees tracking over toes."},
                    {"name": "Lateral Band Walk", "sets": 3, "reps": "10 each direction", "type": "strengthening",
                     "video": "kqeqCHh0SxE", "instruction": "Band around ankles. Side-step maintaining tension. Stay in slight squat."},
                    {"name": "Step-Up", "sets": 3, "reps": "10 each side", "type": "strengthening",
                     "video": "wfhXnLILqdk", "instruction": "Step up onto standard step. Full weight on stepping leg. Control descent."},
                    {"name": "Single-Leg Balance", "sets": 3, "reps": "30s each side", "type": "stability",
                     "video": "vR8C4W0MPOE", "instruction": "Stand on one leg. Maintain balance. Progress by closing eyes."},
                ],
            },
            5: {
                "label": "Minimal/No Pain (VAS 0-0.9)",
                "goal": "Performance, sport-specific, prevention",
                "exercises": [
                    {"name": "Single-Leg Squat", "sets": 3, "reps": "8 each side", "type": "strengthening",
                     "video": "0CodCXxgMk4", "instruction": "Stand on one leg. Lower into controlled squat. Push back up."},
                    {"name": "Walking Lunges", "sets": 3, "reps": "10 each side", "type": "strengthening",
                     "video": "AvBrsGNA7V8", "instruction": "Step forward into deep lunge. Push off and continue walking. Upright posture."},
                    {"name": "Romanian Deadlift", "sets": 3, "reps": "10", "type": "strengthening",
                     "video": "QMe5uQd0WFE", "instruction": "Hinge at hips, lower toward floor. Keep back flat. Full posterior chain exercise."},
                    {"name": "Lateral Band Walk (Deep)", "sets": 3, "reps": "12 each direction", "type": "strengthening",
                     "video": "kqeqCHh0SxE", "instruction": "Heavier band. Deeper squat position. Side-step with purpose."},
                ],
            },
        },
    },
    "PLANTAR_FASCIITIS": {
        "name": "Plantar Fasciitis / Heel Pain",
        "levels": {
            1: {
                "label": "Acute / Severe (VAS 7.5-10)",
                "goal": "Pain relief, reduce inflammation",
                "exercises": [
                    {"name": "Plantar Fascia Massage (Frozen Bottle)", "sets": 3, "reps": "5 min", "type": "mobility",
                     "video": "Uv7Hzp72VG8", "instruction": "Roll frozen water bottle under foot. Apply gentle pressure. Combines ice therapy with massage."},
                    {"name": "Towel Stretch", "sets": 3, "reps": "30s hold", "type": "stretching",
                     "video": "SLk2GjMgOsU", "instruction": "Sit with leg extended. Loop towel around ball of foot. Pull towel gently toward you. Feel stretch in sole and calf."},
                    {"name": "Toe Curls (Towel Scrunch)", "sets": 2, "reps": "10", "type": "strengthening",
                     "video": "67T0vTtMK3Q", "instruction": "Sit with foot on towel. Scrunch towel toward you using toes. Strengthens intrinsic foot muscles."},
                    {"name": "Ankle Circles", "sets": 2, "reps": "10 each direction", "type": "mobility",
                     "video": "KxfFzSOAT7g", "instruction": "Sit with leg extended. Circle ankle clockwise 10 times, then counter-clockwise. Maintains mobility."},
                ],
            },
            2: {
                "label": "Moderate (VAS 5.0-7.4)",
                "goal": "Stretch fascia and calf, begin strengthening",
                "exercises": [
                    {"name": "Calf Stretch (Wall)", "sets": 3, "reps": "30s each side", "type": "stretching",
                     "video": "2_2GMXTc1BE", "instruction": "Face wall, one foot back. Keep back heel down. Lean into wall. Feel calf stretch."},
                    {"name": "Plantar Fascia Stretch", "sets": 3, "reps": "30s hold", "type": "stretching",
                     "video": "Uv7Hzp72VG8", "instruction": "Sit and cross affected foot over knee. Pull toes back toward shin. Feel stretch along arch."},
                    {"name": "Marble Pick-Up", "sets": 2, "reps": "15", "type": "strengthening",
                     "video": "67T0vTtMK3Q", "instruction": "Place marbles on floor. Pick up with toes one at a time. Strengthens foot muscles."},
                    {"name": "Seated Calf Raise", "sets": 3, "reps": "15", "type": "strengthening",
                     "video": "nnPGrBLNlaw", "instruction": "Sit with feet flat. Raise heels off ground. Lower slowly. Builds calf without body weight."},
                ],
            },
            3: {
                "label": "Mild (VAS 3.5-4.9)",
                "goal": "Progressive loading, calf strengthening",
                "exercises": [
                    {"name": "Standing Calf Raise", "sets": 3, "reps": "15", "type": "strengthening",
                     "video": "nnPGrBLNlaw", "instruction": "Stand on edge of step. Rise up on toes. Lower heels below step level slowly."},
                    {"name": "Soleus Stretch", "sets": 2, "reps": "30s each side", "type": "stretching",
                     "video": "2_2GMXTc1BE", "instruction": "Same as calf stretch but bend back knee slightly. Targets deeper soleus muscle."},
                    {"name": "Single-Leg Balance", "sets": 3, "reps": "30s each side", "type": "stability",
                     "video": "vR8C4W0MPOE", "instruction": "Stand on affected foot. Maintain balance. Strengthens foot stabilizers."},
                    {"name": "Eccentric Calf Lower", "sets": 3, "reps": "12 each side", "type": "strengthening",
                     "video": "h7v741oKXu8", "instruction": "Rise on both toes. Shift to one foot. Lower heel slowly (3 seconds). Key exercise for tendon healing."},
                ],
            },
            4: {
                "label": "Low Pain (VAS 1.0-3.4)",
                "goal": "Functional loading, return to walking/running",
                "exercises": [
                    {"name": "Single-Leg Calf Raise", "sets": 3, "reps": "12 each side", "type": "strengthening",
                     "video": "nnPGrBLNlaw", "instruction": "Stand on one foot on step. Full range calf raise. Lower below step level."},
                    {"name": "Toe Walking", "sets": 3, "reps": "20m", "type": "strengthening",
                     "video": "67T0vTtMK3Q", "instruction": "Walk on tiptoes for 20 meters. Strengthens calves and foot intrinsics."},
                    {"name": "Heel Walking", "sets": 3, "reps": "20m", "type": "strengthening",
                     "video": "67T0vTtMK3Q", "instruction": "Walk on heels for 20 meters. Strengthens tibialis anterior. Builds foot control."},
                    {"name": "Mini Squat", "sets": 3, "reps": "12", "type": "strengthening",
                     "video": "wqCvuhfRXRU", "instruction": "Quarter squat with focus on even weight distribution through feet."},
                ],
            },
            5: {
                "label": "Minimal/No Pain (VAS 0-0.9)",
                "goal": "Prevention, return to sport",
                "exercises": [
                    {"name": "Jump Rope (Low Impact)", "sets": 3, "reps": "30s", "type": "plyometric",
                     "video": "hxldG9FX4j8", "instruction": "Light jumping on toes. Build foot and calf endurance. Stop if any pain."},
                    {"name": "Single-Leg Hop", "sets": 3, "reps": "8 each side", "type": "plyometric",
                     "video": "hxldG9FX4j8", "instruction": "Small hops on one foot. Land softly. Tests readiness for running."},
                    {"name": "Eccentric Calf Lower (Weighted)", "sets": 3, "reps": "12", "type": "strengthening",
                     "video": "h7v741oKXu8", "instruction": "Same eccentric lower but holding weights. Progressive overload for tendon."},
                    {"name": "Barefoot Walking on Grass", "sets": 1, "reps": "5 min", "type": "mobility",
                     "video": "67T0vTtMK3Q", "instruction": "Walk barefoot on soft grass. Stimulates foot proprioception. Natural foot strengthening."},
                ],
            },
        },
    },
    "TENNIS_ELBOW": {
        "name": "Tennis Elbow / Lateral Epicondylitis",
        "levels": {
            1: {
                "label": "Acute / Severe (VAS 7.5-10)",
                "goal": "Pain relief, rest from aggravating activities",
                "exercises": [
                    {"name": "Wrist Extensor Stretch", "sets": 3, "reps": "30s hold", "type": "stretching",
                     "video": "g-TN-Ij6zhY", "instruction": "Extend arm straight. Palm facing down. Use other hand to gently bend wrist down. Feel stretch on outer forearm."},
                    {"name": "Wrist Flexor Stretch", "sets": 3, "reps": "30s hold", "type": "stretching",
                     "video": "g-TN-Ij6zhY", "instruction": "Extend arm. Palm facing up. Use other hand to gently bend wrist down. Stretch inner forearm."},
                    {"name": "Fist Clench (Soft Ball)", "sets": 2, "reps": "10, hold 5s", "type": "strengthening",
                     "video": "XcLBNYe-hpc", "instruction": "Squeeze a soft ball or rolled towel gently. Hold 5 seconds. Release. Very light resistance only."},
                    {"name": "Ice Massage", "sets": 3, "reps": "5 min", "type": "mobility",
                     "video": "g-TN-Ij6zhY", "instruction": "Rub ice cup over outer elbow in circles for 5 minutes. Reduces inflammation."},
                ],
            },
            2: {
                "label": "Moderate (VAS 5.0-7.4)",
                "goal": "Begin gentle loading, isometric strengthening",
                "exercises": [
                    {"name": "Isometric Wrist Extension", "sets": 3, "reps": "8, hold 10s", "type": "strengthening",
                     "video": "XcLBNYe-hpc", "instruction": "Rest forearm on table, wrist over edge. Push up against other hand without moving. Hold 10 seconds."},
                    {"name": "Isometric Wrist Flexion", "sets": 3, "reps": "8, hold 10s", "type": "strengthening",
                     "video": "XcLBNYe-hpc", "instruction": "Rest forearm on table. Push wrist down against other hand without moving. Hold 10 seconds."},
                    {"name": "Wrist Extensor Stretch", "sets": 3, "reps": "30s hold", "type": "stretching",
                     "video": "g-TN-Ij6zhY", "instruction": "Extend arm, palm down. Gently bend wrist down with other hand. Hold 30 seconds."},
                    {"name": "Supination/Pronation (No Weight)", "sets": 2, "reps": "10 each", "type": "mobility",
                     "video": "XcLBNYe-hpc", "instruction": "Rest forearm on table. Turn palm up then palm down slowly. Maintain elbow position."},
                ],
            },
            3: {
                "label": "Mild (VAS 3.5-4.9)",
                "goal": "Eccentric loading, progressive strengthening",
                "exercises": [
                    {"name": "Eccentric Wrist Extension", "sets": 3, "reps": "12", "type": "strengthening",
                     "video": "XcLBNYe-hpc", "instruction": "Hold light weight, forearm on table. Use other hand to lift wrist up. Slowly lower under own power (3 seconds). Key exercise."},
                    {"name": "Wrist Curl (Light)", "sets": 3, "reps": "12", "type": "strengthening",
                     "video": "XcLBNYe-hpc", "instruction": "Light dumbbell, forearm on table, palm up. Curl wrist up. Lower slowly."},
                    {"name": "Forearm Pronation/Supination (Hammer)", "sets": 3, "reps": "10 each", "type": "strengthening",
                     "video": "XcLBNYe-hpc", "instruction": "Hold hammer at end of handle. Slowly rotate forearm palm up then palm down. Hammer creates lever resistance."},
                    {"name": "Grip Strengthening (Towel Wring)", "sets": 2, "reps": "10", "type": "strengthening",
                     "video": "XcLBNYe-hpc", "instruction": "Wring wet towel as if squeezing water out. Alternate directions. Functional grip exercise."},
                ],
            },
            4: {
                "label": "Low Pain (VAS 1.0-3.4)",
                "goal": "Functional loading, return to activities",
                "exercises": [
                    {"name": "Eccentric Wrist Extension (Heavier)", "sets": 3, "reps": "15", "type": "strengthening",
                     "video": "XcLBNYe-hpc", "instruction": "Progress weight. Same eccentric lower technique. 3-second controlled descent."},
                    {"name": "Resistance Band Wrist Extension", "sets": 3, "reps": "15", "type": "strengthening",
                     "video": "XcLBNYe-hpc", "instruction": "Step on band. Grip other end. Extend wrist against band resistance."},
                    {"name": "Ball Squeeze (Firm)", "sets": 3, "reps": "12, hold 5s", "type": "strengthening",
                     "video": "XcLBNYe-hpc", "instruction": "Squeeze firm stress ball or tennis ball. Hold 5 seconds. Release. Build grip endurance."},
                    {"name": "Wrist Roller", "sets": 2, "reps": "3 rolls up/down", "type": "strengthening",
                     "video": "XcLBNYe-hpc", "instruction": "Hold rod with weight on string. Roll weight up by rotating wrists. Lower slowly."},
                ],
            },
            5: {
                "label": "Minimal/No Pain (VAS 0-0.9)",
                "goal": "Full function, prevention",
                "exercises": [
                    {"name": "Eccentric Wrist Extension (Progressive)", "sets": 3, "reps": "15", "type": "strengthening",
                     "video": "XcLBNYe-hpc", "instruction": "Continue progressive loading. Maintain eccentric program for tendon health."},
                    {"name": "Push-Up (Modified to Full)", "sets": 3, "reps": "10", "type": "strengthening",
                     "video": "JbOMAwlaVcM", "instruction": "Full or modified push-ups. Tests elbow under body weight. Stop if any lateral elbow pain."},
                    {"name": "Resistance Band Pronation/Supination", "sets": 3, "reps": "12 each", "type": "strengthening",
                     "video": "XcLBNYe-hpc", "instruction": "Band resistance rotation exercises. Functional forearm strengthening."},
                    {"name": "Activity-Specific Training", "sets": 3, "reps": "as tolerated", "type": "strengthening",
                     "video": "XcLBNYe-hpc", "instruction": "Gradually return to specific activities (tennis, typing, gripping) with proper form and breaks."},
                ],
            },
        },
    },
}


def get_exercise_plan(condition: str, level: int) -> dict:
    """Return exercise plan for a given condition and level."""
    cond = EXERCISES.get(condition)
    if not cond:
        return {"error": f"Unknown condition: {condition}"}
    lvl = cond["levels"].get(level)
    if not lvl:
        return {"error": f"Invalid level {level} for {condition}"}
    return {
        "condition": cond["name"],
        "level": level,
        "label": lvl["label"],
        "goal": lvl["goal"],
        "exercises": lvl["exercises"],
    }


def determine_level(pain_vas: float, age: int, is_chronic: bool, comorbidity_count: int) -> int:
    """
    Evidence-based exercise level assignment.
    References: Boonstra 2014 VAS cutoffs, ACSM age guidelines, ADA comorbidity modifiers.
    """
    # Boonstra 2014 VAS cutoffs
    if pain_vas >= 7.5:
        level = 1
    elif pain_vas >= 5.0:
        level = 2
    elif pain_vas >= 3.5:
        level = 3
    elif pain_vas >= 1.0:
        level = 4
    else:
        level = 5

    # Chronicity modifier
    if is_chronic and pain_vas < 5.0:
        level = min(level + 1, 5)  # Chronic low pain can progress faster
    elif not is_chronic and pain_vas >= 5.0:
        level = max(level - 1, 1)  # Acute moderate pain: be more conservative

    # ACSM age guideline
    if age >= 65:
        level = max(level - 1, 1)
    elif age >= 50 and comorbidity_count >= 2:
        level = max(level - 1, 1)

    # ADA comorbidity modifier
    if comorbidity_count >= 3:
        level = max(level - 1, 1)

    # Level 5 only for younger patients
    if level == 5 and age >= 50:
        level = 4

    return level
