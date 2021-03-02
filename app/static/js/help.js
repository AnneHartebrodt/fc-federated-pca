var updates = [
    {
      id: 23,
      badge: "Update",
      title: "Evaluate code into the console",
      body:  "Custom Console beta is getting more stable and feature-rich. Just added the ability to evaluate code in the console.",
      highlight: {
        target: "#console"
      }
    },
    {
      id: 22,
      badge: "New",
      title: "Console in the editor",
      body:  "Introducing the first beta of the editor console - it's going to show you logs, warnings, errors without the need of opening full devtools.<br><br> Console is avaialble for all users during beta, after that it'll be available for JSFiddle supporters.",
      highlight: {
        target: "*[data-popover-trigger='editor-settings']"
      }
    },
    {
      id: 21,
      badge: "New",
      title: "More user's social links (Dev.to, SO...)",
      body:  "You can add more of your social links `Settings / Social Media`, for Dev.to, Stack Overflow and Medium. These will be displayed on the profile section in Editor's sidebar and your public profile.",
    },
    {
      id: 20,
      badge: "Update",
      title: "Refactored Unsaved Drafts feature",
      body:  "Unsaved drafts feature is completely rewritten with 100% fewer bugs and 10x more maintainable codebase – as the author of the previous one, I had hard times figuring out what it does 🥴",
    },
    {
      id: 19,
      badge: "Update",
      title: "Load Mode is retired",
      body:  "Load-modes such as: domready, onload, bottom Body, bottom Head have been retired. Very little users used them, and caused confusion to new devs. All fiddles will now run in a single, safe load mode.",
    },
    {
      id: 18,
      badge: "New",
      title: "PRO features",
      body:  "PRO account introduces Private fiddles, Groups and private groups (with global default privacy), no ads, Console (soon). <a href='/extra/' target='_new'>Upgrade to PRO</a>",
    }
  ]

  var UpdatesWidget = function(options){
    if (updates.length <= 0) return false

    var selectedItem  = 0
    var currentUpdate = updates[selectedItem]
    var lastSeenId    = window.localStorage.getItem("last_seen_update")
    var template      = {}

    var element = {
      updates:     document.querySelector("#app-updates"),
      highlighter: document.createElement("div")
    }

    // generic template for the widget
    template.title   = "<strong class='badge'>#{badge}</strong> #{title}"
    template.body    = "<p>#{body}</p>"
    template.actions = "<div class='updateActions'><a href='' class='previous'>Previous update</a><a href='' class='dismiss'>Got it</a></div>"
    template.full    = template.title + template.body + template.actions
    template.body    = "<div class='body'>" + template.full + "</div>"
    template.update  = "<div class='bodyCont'>" + template.body + "</div>"

    // inject the highlighter
    element.highlighter.id = "app-updates-highlighter"
    document.body.appendChild(element.highlighter)

    var dismissUpdate = function(event){
      event.preventDefault()
      event.stopPropagation()

      window.localStorage.setItem("last_seen_update", currentUpdate.id)
      element.updates.classList.add("hidden")

      Track.ui("Update dismissed")
    }

    var showHighlighter = function(event){
      event.preventDefault()
      event.stopPropagation()

      var target  = document.querySelector(currentUpdate.highlight.target)
      var rect    = target.getBoundingClientRect()
      var visible = !element.updates.classList.contains("hidden")

      element.highlighter.style.top    = rect.top + "px"
      element.highlighter.style.left   = rect.left + "px"
      element.highlighter.style.width  = rect.width + "px"
      element.highlighter.style.height = rect.height + "px"

      // only highlight before updater is dismissed
      if (visible){
        element.highlighter.classList.add("show")
      }
    }

    var hideHighlighter = function(event){
      element.highlighter.classList.remove("show")
    }

    var setUpdate = function(event){

      if (event){
        event.preventDefault()
        event.stopPropagation()

        selectedItem = selectedItem + 1

      } else {
        selectedItem = 0
      }

      currentUpdate = updates[selectedItem]

      // update the title
      var update = template.update
        .replace("#{badge}", currentUpdate.badge)
        .replace("#{title}", currentUpdate.title)
        .replace("#{body}",  currentUpdate.body)

      element.updates.innerHTML = update

      // dismiss update and save ID for future reference
      var dismiss = document.querySelector(".updateActions .dismiss")
      dismiss.addEventListener("click", dismissUpdate)

      var previous = document.querySelector(".updateActions .previous")
      previous.addEventListener("click", setUpdate)
    }

    setUpdate()

    // manage highlighter
    if (currentUpdate.highlight){
      element.updates.addEventListener("mouseover", showHighlighter)
      element.updates.addEventListener("mouseout", hideHighlighter)
    }

    // remove hidden class if user hasn't seen the latest update
    if (parseInt(lastSeenId) !== currentUpdate.id){
      element.updates.classList.remove("hidden")
    }
  }

  window.addEventListener("DOMContentLoaded", UpdatesWidget)
