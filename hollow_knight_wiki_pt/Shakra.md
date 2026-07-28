# Shakra

Shakra é uma Mercadora e chefe em Hollow Knight: Silksong. Ela vende mapas e ferramentas de cartografia em troca de Rosários. Sua localização é indicada pelos anéis que ela joga, espalhados pelos arredores, e pelo som de seu canto à distância.

 Contexto 
Shakra é uma guerreira e navegadora de uma tribo na borda de Fiarlongo.Diário do Caçador:"Guerreira cartógrafa de uma tribo na borda de Fiarlongo. Suas habilidades em batalha poderiam rivalizar com as dos melhores do reino. Sua tribo valoriza a proficiência em combate Shakra: Vencida pela idade... Minha tribo chamaria isso de vergonha e suas integrantes se referem umas às outras pela arma que carregam.Shakra: Sou Shakra, a Que Empunha Anéis..Shakra: Bem-vinda, Garotinha da Agulha.

 Eventos no jogo 
Shakra pode ser encontrada em vários locais de Fiarlongo. Com exceção do Vale dos Ossos e de Campânula, assim que Shakra é encontrada em um local, ela segue adiante e não retorna àquele lugar.FSM mapper_evaluate_location in fsmtemplates_assets_mapper.bundle. Ela pode deixar de aparecer em um local se certas condições forem cumpridas; nesses casos, os itens daquela área são automaticamente adicionados à sua loja e podem ser comprados no próximo encontro.

Shakra pode ser encontrada pela primeira vez na Medula. Após a Besta dos Sinos ser derrotada, ela se estabelece em uma saliência a leste do Vale dos Ossos. Se Shakra estiver fora, pode ser chamada de volta batendo no seu mastro de argolas. Assim que a Viúva é derrotada, ou se o Desejo O Tirano Terrível for concluído,FSM Mapper Control in bonetown.bundle. Shakra deixa o Vale dos Ossos e não retorna, mesmo quando chamada.

Shakra auxilia na luta da arena na Trilha de Skarr se Hornet não tiver visitado Pântano Cinzento, Campânula ou Cascomadeira.FSM CallAlly in ant_04_mid.bundle. Se Shakra não aparecer para a luta, ela pode ser encontrada em uma seção posterior da Trilha de Skarr, no longo túnel que leva à direita para a Capela da Fera.

Após a derrota da Viúva, Shakra reside em uma saliência a leste de Campânula. Semelhante ao Vale dos Ossos, quando Shakra está fora, ela pode ser chamada de volta batendo no seu mastro de argolas.

Se os pré-requisitos para o Desejo Fim da Trilha forem cumpridos, Shakra desaparece de todos os locais e não retornará até que o Desejo seja concluído.GameManager.TimePasses() calls MapperLeaveAll(). Após a conclusão do Desejo, Shakra dá a Hornet a ferramenta Anel de Arremesso e pode ser chamada para auxiliar na luta no Fórum dos Salões Supremos. Isso substitui o aparecimento de Garmond & Zaza para ajudar, caso a missão deles também tenha sido concluída.FSM Aid NPC Control in hang_06.bundle.

Após a conclusão do Desejo, Shakra também pode ser encontrada logo na entrada do Pântano Cinzento para Campânula, tocando seu poste, onde ela desafia Hornet para um duelo amistoso, que pode ser repetido após a vitória. Não há recompensa ou prêmio por vencer o duelo. O duelo deixa de ser acessível assim que o Ato 3 tem início.

Após o início do Ato 3, Shakra assume o papel de defensora de Campânula e só permanece na cidade ocasionalmente,FSM Mapper Control in belltown.bundle. podendo às vezes ser vista eliminando inimigos nas entradas da cidade, no Pântano Cinzento e em Cascomadeira.GameObject Shakra Guard Scene checks mapperLocationAct3 in greymoor_08.bundle and shellwood_01.bundle.

 Comportamento e Táticas 
Shakra possui os seguintes movimentos, tanto como aliada quanto como oponente:
 Teletransporte: Shakra se teletransporta rapidamente de 1 a 3 vezes entre cada ataque, como sua principal forma de locomoção. A cada teletransporte, ela sempre mantém uma distância de seu oponente.
 Arremesso de Argola: Shakra se teletransporta para o ar e rapidamente lança 1 ou 2 argolas em rápida sucessão contra o oponente. Essas argolas quicam uma vez no chão e não são afetadas pela gravidade.
 Explosão de Argola: Shakra se teletransporta diretamente acima do oponente, faz uma breve pausa e então se arremessa ao chão, criando uma explosão de energia em forma de argola ao seu redor. Contra Hornet, este ataque causa .

Quando aliada de Hornet contra outros inimigos, Shakra ocasionalmente bloqueia ataques ou projéteis inimigos. Após bloquear 15 vezes, ela fica atordoada e cai de joelhos. Ela se recupera após 6 segundos, ou instantaneamente se Hornet usar uma Amarração perto dela. 

Durante o treino com ela no Pântano Cinzento, Shakra também possui os seguintes movimentos:

 Investida de Argola: Shakra se teletransporta para o chão e avança rapidamente em direção a Hornet, criando um grande pulso de energia com suas argolas no final da investida, que causa . Se Hornet estiver atrás dela, Shakra complementa o ataque lançando uma argola na direção oposta à investida.
Se Hornet for derrotada, ela simplesmente desmaia e acorda ao lado da argola do desafio. Portanto, este duelo pode ser perdido no Modo Alma de Aço sem que o arquivo de save seja perdido permanentemente.

 Itens 

 Mapas 
 Item Custo Descrição de Shakra Requiresshopitems.bundle checks flags SeenMapperIn[Area] for maps to appear in shop. These flags are set either by meeting Shakra directly in the areas, or by fsmtemplates_assets_mapper.bundle when it checks various other flags. center|72x72px
Mapa das Terras Musgosas  Essas cavernas tomadas por vegetação oferecem poucos desafios para uma guerreira habilidosa. Um lugar para reflexão, talvez. center|72x72px
Mapa da Medula  Estradas decadentes construídas sobre as carapaças de antigos insetos. Toda Fiarlongo descansa sobre estas frágeis fundações. center|72x72px
Mapa das Docas Profundas  Pensei que essas docas fossem menores, quando passei aqui a primeira vez. Agora sinto que grande parte da estrutura se oculta abaixo do lago derretido. Encontrar Shakra nas Docas Profundas, ou ativar o Templo do Campanário na área, ou derrotar a Viúva center|72x72px
Mapa dos Campos Longínquos  Carapaças-vermelhas ferozes se aninham nessas cavernas selvagens. A batalha contra eles é muito intensa, e as criaturas são mais cruéis que as das ossudas terras medulares. Encontrar Shakra nos Campos Longínquos, ou derrotar a Viúva, ou obter o Manto da Errante, ou entrar na Cidadela. center|72x72px
Mapa do Covil dos Vermes  Cavernas repletas de vermes, trêmulas e instáveis. Lá restam fracos vestígios de que peregrinos um dia viajaram por esses caminhos estreitos. Encontrar Shakra nas Covil dos Vermes ou entrar na Cidadela center|72x72px
Mapa da Trilha de Skarr  Caminhos escavados dos carapaças-vermelhas. Seus armazéns e santuários são frequentes por toda parte. Esses túneis devem dar a eles uma passagem rápida até os campos abaixo. Encontrar Shakra na Trilha de Skarr center|72x72px
Mapa do Pântano Cinzento
Também concede mapa para o Bosque dos Lumes.  Cavidades largas e escuras, cheias de trapos e poeira. Os insetos que um dia cuidaram destas terras certamente se perderam. Encontrar Shakra no Pântano Cinzento, ativar o Templo do Campanário na área ou obter a Turbilhão de Fios center|72x72px
Mapa da Campânula  Uma aldeia construída dentro do espesso veio de sinos que atravessa o núcleo de Fiarlongo. Dá para imaginar, por que construíram tantos, e para que propósito? Entrar em Campânula center|72x72px
Mapa de Cascomadeira  Estradas emaranhadas entre espinheiros e raízes. A flora daqui é tão mortal quanto as criaturas que fizeram daqui seu lar. Encontrar Shakra em Cascomadeira, obter a Garra Aderente ou derrotar a Viúva center|72x72px
Mapa dos Degraus Devastados  Enormes cavernas que levam à Cidadela de Fiarlongo acima. As estradas estão lentamente sendo devoradas pela areia e o vento uivante. Encontrar Shakra nos Degraus Devastados ou derrotar a Última Juiza center|72x72px
Mapa do Caminho dos Pecadores  Velhas estradas e passagens tomadas por baratas e seus cuidadores. Os caminhos estão cobertos por uma camada grossa de sujeira. Encontrar Shakra em Caminho dos Pecadores center|72x72px
Mapa do Monte Plumídio  TO cume irregular pairando sobre toda Fiarlongo. Seus ventos cortantes e frio intenso perfurariam a carapaça mais forte. Encontrar Shakra no Monte Plumídio ou obter o Manto de Plumídio center|72x72px
Mapa das Areias de Karak  Penhascos encrustados acima daqueles degraus uivantes. Sinais sugerem que grandes guerreiros já governaram este lugar tortuoso, ainda que a areia tenha apagado muitas de suas marcas. Encontrar Shakra nas Areias de Karak ou derrotar a Mosquicórnio Furioso na área center|72x72px
Mapa do Bilebrejo  Pântanos nascidos à sombra da Cidadela. Há evidências que a água daqui um dia já foi cristalina. Encontrar Shakra em Bilebrejo ou derrotar Groal, o Magnífico

 Ferramentas de Cartografia 
 Item Custo Descrição de Shakra Requer center|link=Map and Quill (Silksong)|72x72px
Pena  Com essa pena, você pode adicionar quaisquer áreas que descobrir aos mapas que comprou de mim. Nós arrancamos essas penas dos Golpeni caçados pela minha tribo. As hastes ocas delas são a ferramenta de mapeamento perfeita. center|link=Compass|72x72px
Bússola  Acompanhe sua localização nestas terras tortuosas com uma bússola de osso. Cada membro da nossa tribo pode fabricá-las. Eu posso te dar a minha, por um preço justo.

 Pinos do mapa 
 Item Custo Descrição de Shakra Requer center|72x72px
Pinos de Bancos  Ao viajar por terras hostis, é importante lembrar de lugares seguros para acampar.
Esses pinos marcarão bancos e outros lugares de descanso em seu mapa. center|72x72px
Pinos das Vias Campanárias  As Vias Campanárias, veios dourados que atravessam as terras. Supostamente, elas já foram usadas para viajar?
Esses pinos irão marcar estações no seu mapa.Derrotar a Besta do Sino center|72x72px
Pinos de Ventrícula  Como você pediu, esses pinos marcarão as estações de viagem dentro daquela estrutura horrenda de aço e vapor. Após abrir a primeira Ventrícula, Hornet solicitará os Pinos de Ventrícula na próxima conversa com Shakra, mas os pinos só serão vendidos em um encontro subsequente. center|72x72px
Pinos de Comerciantes  Muitos insetos de Fiarlongo têm equipamentos e itens úteis para negociar. Seria bom manter um registro de seus locais com esse pino.
Esses pinos marcarão comerciantes em seu mapa. Entrar nas Docas Profundas, nas Covil dos Vermes ou no Pântano Cinzento center|72x72px
Marcador de Carapaça  Você pode usá-los para marcar lugares importantes ou lembretes no seu mapa.
Modelei esses marcadores com base no brilho da minha própria carapaça. Talvez você pense em mim quando usá-los. center|72x72px
Marcador de Anel  Você pode usá-los para marcar lugares importantes ou lembretes no seu mapa.
Costumo usar esses para marcar os locais de adversários dignos. Entrar nas Docas Profundas ou no Covil dos Vermes center|72x72px
Marcador de Caçada  Você pode usá-los para marcar lugares importantes ou lembretes no seu mapa.
A carapaça dos caçadores-vermelhos resulta em um marcador bem vívido. Encontrar Shakra na Trilha de Skarr ou derrotar a Viúva center|72x72px
Marcador Escuro  Você pode usá-los para marcar lugares importantes ou lembretes no seu mapa.
Esse material de carapaça-escura é frio ao toque, e mais resiliente do que parece. Entrar na Cidadela center|72x72px
Marcador de Bronze  Você pode usá-los para marcar lugares importantes ou lembretes no seu mapa.
Eu fiz esses com as carcaças de antigos sinos. Uma tarefa bem difícil, então o preço reflete esse esforço extra. Entrar na Cidadela

 Localizações 
Shakra pode ser encontrada em vários locais de Fiarlongo.

 Conquistas 

 Curiosidades 
 Shakra foi revelada oficialmente em uma postagem de blog da Team Cherry:
"Feroz e intimidadora, Shakra é uma guerreira em busca de seu mestre, que desapareceu em circunstâncias misteriosas. O clã de Shakra é formado por lutadores habilidosos que sabem se virar nos territórios selvagens do reino. Algo útil para Hornet: cada membro do clã também domina um Ofício, e a maestria de Shakra em cartografia será inestimável na aventura da protagonista."
 Se qualquer inimigo se aproximar demais de Shakra a qualquer momento, ela se move para atacá-lo com suas Argolas de Arremesso.
 Shakra só canta se o Agulino for tocado fora de combate. Ela não reage ao instrumento durante uma batalha, seja contra inimigos ou contra Hornet.
 Shakra pode ter diálogos diferentes dependendo do seu modo de animação atual. Os mais comuns são o modo em pé e o modo sentada. Na maioria dos locais, isso não importa muito, pois ela usa apenas um único modo; mas no Vale dos Ossos e em Campânula, isso pode afetar os diálogos, já que esses locais usam ambos os modos.FSMs Mapper NPC - Dialogue and Mapper Sit NPC - Dialogue in bonetown.bundle and belltown.bundle. O modo em pé é ativado quando Shakra é chamada de volta à cidade com seu mastro de argolas, enquanto o modo sentado é usado quando Hornet chega à área e Shakra já está lá. É importante notar que, se Shakra estiver em uma dessas cidades e Hornet descansar em um banco fora da cidade onde Shakra se encontra, há uma chance de 50% de Shakra sair dali e não retornar, a menos que seja chamada novamente com o mastro de argolas.GameManager.TimePasses() sets flag mapperAway.
 O ícone dos Alfinetes de Ventrica vendidos na loja de Shakra está com cores incorretas: os alfinetes reais no mapa são pretos, mas são mostrados como cinza na loja.
 O ícone correto (preto) realmente existe nos arquivos do jogo, mas parece estar nomeado incorretamente e não é utilizado.
A localização inicial de Shakra no Vale dos Ossos era diferente: ela ficava sentada no meio do assentamento, e não no topo da pedra à direita dele.
No Monte Plumídio, se Hornet obtiver o Manto de Plumídio, o acampamento de Shakra desaparecerá, junto com a função de banco da pedra próxima, embora a pedra em si permaneça.

 Notas 

 Referências de código 

es:Shakra
fr:Shakra

Categoria:Inimigos (Silksong)
Categoria:Chefes (Silksong)
Categoria:NPCs (Silksong)
