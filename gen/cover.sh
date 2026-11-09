#!/bin/bash
# $1 = id, $2 = сцена. Генерация обложки через Codex imagegen (подписка, бесплатно).
id=$1; scene=$2; case $id in V*) out=/Users/artemgalimov/Sites/avtostil-kontent/gen/vk/$id.png; FMT="portrait 4:5";; *) out=/Users/artemgalimov/Sites/avtostil-kontent/gen/covers/$id.png;; esac
[ -s "$out" ] && exit 0
P="Realistic high-quality photo, ${FMT:-horizontal 4:3}, looks like a real candid shot by a good photographer. $scene Modern clean cars 2022-2025, ordinary people of Russia, natural lively colors, not grey, not gloomy, not post-apocalyptic. No text, no letters, no logos, no brand emblems, no license plates (plate area out of frame or blank), no watermarks."
codex exec -m gpt-5.6-luna -c model_reasoning_effort=low -s workspace-write -C /Users/artemgalimov/Sites/avtostil-kontent --skip-git-repo-check "Скопируй текст между маркерами в imagegen дословно, символ в символ. Не перефразируй, не сокращай, не дополняй.

=== НАЧАЛО ПРОМТА ===
$P
=== КОНЕЦ ПРОМТА ===

Сохрани как $out
Затем приведи точную строку, которую передал в imagegen." > /Users/artemgalimov/Sites/avtostil-kontent/gen/log/$id.txt 2>&1
[ -s "$out" ] && echo "OK $id" || echo "FAIL $id"
