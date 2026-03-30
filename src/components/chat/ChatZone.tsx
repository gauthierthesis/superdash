"use client"

import { useEffect, useRef } from "react"
import { useConversationStore } from "@/store/useConversationStore"
import { ScrollArea } from "@/components/ui/scroll-area"
import ChatInput from "./ChatInput"
import QuickActionButton from "./QuickActionButton"

const QUICK_ACTIONS = [
  { label: "Réaliser un commentaire de décision", icon: "📄" },
  { label: "Rechercher une jurisprudence", icon: "🔍" },
  { label: "Réviser mes cours grâce à des questions", icon: "🎯" },
  { label: "Réaliser une fiche synthétisée de jurisprudence", icon: "📋" },
  { label: "Préparer un sujet d'examen", icon: "🎓" },
]

export default function ChatZone() {
  const { conversations, activeConversationId, addMessage } =
    useConversationStore()

  const activeConversation = conversations.find(
    (c) => c.id === activeConversationId
  )

  const bottomRef = useRef<HTMLDivElement>(null)

  // Scroll automatique vers le bas à chaque nouveau message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [activeConversation?.messages])

  const handleSend = async (content: string) => {
    if (!activeConversationId) return

    // Ajoute le message de l'utilisateur
    addMessage(activeConversationId, {
      id: crypto.randomUUID(),
      role: "user",
      content,
      createdAt: new Date(),
    })

    // TODO : connecter Mistral ici (étape suivante)
    // Pour l'instant on simule une réponse
    setTimeout(() => {
      addMessage(activeConversationId, {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "Je suis Sapient'IA, je traite votre question...",
        createdAt: new Date(),
      })
    }, 1000)
  }

  const handleQuickAction = (label: string) => {
    if (!activeConversationId) return
    handleSend(label)
  }

  return (
    <div className="flex flex-col h-screen flex-1 bg-neutral-50">

      {/* Zone messages */}
      <ScrollArea className="flex-1 px-6 py-4">
        {!activeConversation ? (
          // Écran d'accueil — aucune conversation active
          <div className="flex flex-col items-center justify-center h-full gap-6 mt-20">
            <h2 className="text-2xl font-bold text-neutral-700">
              Nouvelle conversation
            </h2>
            <div className="flex flex-wrap justify-center gap-3 max-w-2xl">
              {QUICK_ACTIONS.map((action) => (
                <QuickActionButton
                  key={action.label}
                  icon={action.icon}
                  label={action.label}
                  onClick={() => handleQuickAction(action.label)}
                />
              ))}
            </div>
          </div>
        ) : (
          // Affichage des messages
          <div className="flex flex-col gap-4 max-w-2xl mx-auto">
            {activeConversation.messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${
                  message.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`px-4 py-2 rounded-2xl max-w-[75%] text-sm ${
                    message.role === "user"
                      ? "bg-red-600 text-white rounded-br-none"
                      : "bg-white border border-neutral-200 text-neutral-700 rounded-bl-none"
                  }`}
                >
                  {message.content}
                </div>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </ScrollArea>

      {/* Zone de saisie */}
      <ChatInput
        onSend={handleSend}
        disabled={!activeConversationId}
      />
    </div>
  )
}