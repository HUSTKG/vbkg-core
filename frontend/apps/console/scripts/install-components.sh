#!/bin/bash
components=(
  "form"
  "input"
  "button"
  "label"
  "card"
  "navigation-menu"
  "dropdown-menu"
  "tabs"
  "scroll-area"
  "table"
  "avatar"
  "badge"
  "separator"
  "alert"
  "toast"
  "progress"
  "skeleton"
  "dialog"
  "alert-dialog"
  "sheet"
  "select"
  "checkbox"
  "radio-group"
)

for component in "${components[@]}"
do
  echo "Installing $component..."
  bunx --bun shadcn@latest add $component -y
done
