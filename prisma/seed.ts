import { PrismaClient, IssueStatus, IssuePriority, MemberRole } from "../app/generated/prisma";

const prisma = new PrismaClient();

async function main(): Promise<void> {
  // Clean up in dependency order before seeding
  await prisma.comment.deleteMany();
  await prisma.issue.deleteMany();
  await prisma.column.deleteMany();
  await prisma.board.deleteMany();
  await prisma.teamMember.deleteMany();
  await prisma.session.deleteMany();
  await prisma.account.deleteMany();
  await prisma.user.deleteMany();
  await prisma.team.deleteMany();
  await prisma.organization.deleteMany();

  // 1 Organization
  const organization = await prisma.organization.create({
    data: {
      name: "TaskFlow Demo Org",
    },
  });

  // 1 Team
  const team = await prisma.team.create({
    data: {
      name: "Engineering",
      organizationId: organization.id,
    },
  });

  // 1 User (owner)
  const user = await prisma.user.create({
    data: {
      name: "Demo User",
      email: "demo@taskflow.dev",
    },
  });

  // Add user as team owner
  await prisma.teamMember.create({
    data: {
      teamId: team.id,
      userId: user.id,
      role: MemberRole.OWNER,
    },
  });

  // 1 Board
  const board = await prisma.board.create({
    data: {
      name: "Sprint 1",
      teamId: team.id,
    },
  });

  // 3 Columns: Todo, In Progress, Done
  const todoColumn = await prisma.column.create({
    data: {
      name: "Todo",
      order: 1,
      boardId: board.id,
      teamId: team.id,
    },
  });

  const inProgressColumn = await prisma.column.create({
    data: {
      name: "In Progress",
      order: 2,
      boardId: board.id,
      teamId: team.id,
    },
  });

  const doneColumn = await prisma.column.create({
    data: {
      name: "Done",
      order: 3,
      boardId: board.id,
      teamId: team.id,
    },
  });

  // 3 Issues distributed across columns
  await prisma.issue.create({
    data: {
      title: "Set up authentication",
      description: "Implement Auth.js with Supabase adapter and GitHub OAuth provider.",
      status: IssueStatus.TODO,
      priority: IssuePriority.HIGH,
      order: 1,
      boardId: board.id,
      columnId: todoColumn.id,
      teamId: team.id,
      createdById: user.id,
    },
  });

  await prisma.issue.create({
    data: {
      title: "Build kanban board UI",
      description: "Create the drag-and-drop kanban board using dnd-kit and Zustand.",
      status: IssueStatus.IN_PROGRESS,
      priority: IssuePriority.HIGH,
      order: 1,
      boardId: board.id,
      columnId: inProgressColumn.id,
      teamId: team.id,
      assigneeId: user.id,
      createdById: user.id,
    },
  });

  await prisma.issue.create({
    data: {
      title: "Initialize Next.js project",
      description: "Bootstrap the Next.js 15 app with TypeScript, Tailwind, and shadcn/ui.",
      status: IssueStatus.DONE,
      priority: IssuePriority.MEDIUM,
      order: 1,
      boardId: board.id,
      columnId: doneColumn.id,
      teamId: team.id,
      assigneeId: user.id,
      createdById: user.id,
    },
  });
}

main()
  .then(async () => {
    await prisma.$disconnect();
  })
  .catch(async (error: unknown) => {
    process.stderr.write(
      `Seed error: ${error instanceof Error ? error.message : String(error)}\n`
    );
    await prisma.$disconnect();
    process.exit(1);
  });
