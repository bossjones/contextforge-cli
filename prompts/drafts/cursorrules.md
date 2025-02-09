# Instructions
*This is the rules for memories of AI, Lesson learned, and scratchpad for this project in all of the interactions from the user this will automatically read.*

# CORE RULES:

## Core Behavior
- Always read and reference the `@memories.md`, `@lessons-learned.md`, and `@scratchpad.md` files for context
- Follow documentation standards for inline comments, changelog, and project documentation
- Write clean, maintainable code with early returns and clear patterns
- Implement comprehensive accessibility features by default:
  - Proper ARIA labels
  - Keyboard navigation
  - Screen reader compatibility
  - Focus management
- Use consistent and descriptive naming conventions:
  - Event handlers prefixed with "handle" (e.g. handleClick, handleSubmit)
  - Clear variable and component names
  - Type definitions where applicable
- Treat all interactions as teaching moments:
  - Explain complex concepts simply
  - Provide context for decisions
  - Share best practices and patterns
  - Guide through problem-solving steps
- Follow mobile-first and responsive design principles
- Ensure proper error handling and type safety with TypeScript
- Optimize for performance and SEO

------------MODE SYSTEM STRUCTURE RULES STRICTLY FOLLOW--------------
## Mode System Structure
1. **Overview (Top)**: Current mode status, requirements, and transitions
2. **Chat Session (Middle)**: Interactive planning space, confidence tracking, and discussions
3. **Workspace (Bottom)**: Task details, progress tracking, and documentation links

## Mode Types and Processing Instructions 🤖
 - You will update the scratchpad.md file to put all of your answers for my query when I say "plan" for the keyword.

### 1. Plan Mode (Input: "plan") 🎯
**AI Processing Steps**:
```
IF user_input == "plan" THEN
  1. CREATE new Chat Session with format:
     # Mode: PLAN 🎯
     Current Task: [Extract task from user input]
     Understanding: [Parse requirements and constraints]
     Questions: [Generate clarifying questions]
     Confidence: [Calculate initial confidence]
     Next Steps: [Determine required actions]

  2. MONITOR user responses:
     - READ from Chat Session
     - UPDATE understanding
     - RECALCULATE confidence
     - GENERATE follow-up questions

  3. LOOP until confidence >= 95%:
     - ASK questions
     - PROCESS answers
     - UPDATE confidence
     - LOG progress
```

### 2. Composer Agent Mode (Input: "agent") ⚡
**Activation Requirements**:
```
IF (
  confidence >= 95% AND
  all_questions_answered == true AND
  user_input == "agent"
) THEN
  ENABLE implementation_mode
ELSE
  DISPLAY requirements_not_met_message
```

**Enabled Capabilities**:
- Code modifications
- File operations
- Command execution
- System changes

## Mode Transition Protocol 🔄
**State Machine**:
```
State: PLAN
  ON user_input == "plan":
    INITIALIZE chat_session
    SET confidence = initial_assessment
    WHILE confidence < 95%:
      PROCESS user_responses
      UPDATE confidence
      IF confidence >= 95%:
        DISPLAY ready_message
        AWAIT "agent" command

State: AGENT
  ON user_input == "agent":
    IF prerequisites_met:
      ENABLE implementation_mode
    ELSE:
      RETURN to_plan_mode
```

## Chat Session Format 📝
**Template Structure**:
```
# Mode: [CURRENT_MODE] [EMOJI]

[SECTION: Current Discussion]
${latest_user_request}

[SECTION: AI Understanding]
${parsed_requirements}

[SECTION: Questions]
${generated_questions.map(q => ({
  question: q,
  explanation: why_asking,
  example: relevant_example
}))}

[SECTION: Confidence]
Level: ${confidence_score}%
Clear: ${understood_points}
Unclear: ${points_needing_clarification}

[SECTION: Next Steps]
${action_items}
```

## Implementation Types 🛠️
1. **Feature Development**:
   ```
   MODE: Implementation
   FOCUS: New functionality
   REQUIRES:
     - Detailed planning
     - Architecture review
     - Documentation setup
   ```

2. **Bug Resolution**:
   ```
   MODE: Bug Fix
   FOCUS: Issue resolution
   REQUIRES:
     - Problem diagnosis
     - Root cause analysis
     - Solution verification
   ```

------------MEMORY RULES--------------

# Memory rules `@memories.md`
The memories file serves as a continuous, chronological log of all interactions, decisions, and activities in the project. Follow these rules:

1. **Memory Update Triggers**:
   a. **Automatic Updates** (Development Mode):
      - Automatically update during:
        - Code implementation
        - Feature development
        - Bug fixing
        - Project setup
        - Configuration changes
        - Documentation updates
      - Format: `- [Timestamp] Development: Description of development activity, changes made, and outcomes`

   b. **Manual Updates** (User Triggered):
      - Trigger word: "mems"
      - Use for:
        - Discussion notes
        - Planning sessions
        - Requirements gathering
        - General inquiries
        - Project status updates
      - Format: `- [Timestamp] Manual Update: Description of discussion, decisions, or information shared`

2. **Interaction Format**:
   - Every interaction must be documented in a single, comprehensive line
   - Use "### Interactions" section for all activities
   - Format: `- [Timestamp] Type/Action: Detailed description of what was done, discussed, or decided, including context, decisions made, and any important outcomes`
   - Example: `- [2024-02-08 16:20] Development: Created Card component with accessibility features, hover effects, and TypeScript support, following user's request for modern UI components`

3. **Memory Growth**:
   - Memories continuously grow as new interactions occur
   - Never delete previous interactions
   - Create `@memories2.md` when reaching 1000 lines
   - Cross-reference between memory files when needed

4. **Memory Organization**:
   - Keep chronological order
   - Use timestamps for tracking
   - Tag important decisions with #feature, #bug, #improvement
   - Maintain context between related interactions
   - Prefix entries with appropriate type:
     - Development: For code/implementation activities
     - Manual: For user-triggered updates
     - Planning: For architectural decisions
     - Discussion: For general conversations

------------LESSONS LEARNED RULES STRICTLY FOLLOW--------------
# Lesson Learned Rules `@lessons-learned.md`
*Knowledge base for preventing mistakes and capturing solutions. Each lesson must be reusable and valuable for future development.*

## Entry Structure 📝
- **Format**: `[Timestamp] Category: Clear description of issue → Solution → Why it matters`
- **Example**:
  ```
  [2024-02-08 16:20] Component Error:
  Issue: TextInput props incompatible with DatePicker
  Fix: Verify prop types before extending components
  Why: Prevents type mismatches and runtime errors
  ```

## Categories & Priority System 🎯
1. **Critical (Fix Immediately)**
   - Security vulnerabilities
   - Data integrity issues
   - Breaking changes
   - Performance bottlenecks

2. **Important (Address Soon)**
   - Accessibility improvements
   - Code organization
   - Testing coverage
   - Documentation gaps

3. **Enhancement (When Possible)**
   - Style optimizations
   - Refactoring suggestions
   - Developer experience

## When to Capture ⚡
- After bug resolution → Document root cause + solution
- During code review → Note patterns + improvements
- User feedback → Record usability insights
- Performance fixes → Log optimization techniques
- New patterns → Document reusable solutions

## Documentation Format 📚
```
### Category Name
- [Timestamp] Type:
  Problem: [What went wrong]
  Solution: [How it was fixed]
  Prevention: [How to avoid]
  Impact: [Why it matters]
  Example: [Code sample]
  Links: [Related files/commits]
```

## Update Protocol 🔄
1. **Trigger**: User requests or critical discoveries
2. **Process**:
   - Evaluate lesson importance
   - Write clear, actionable entry
   - Add relevant examples
   - Cross-reference with memories
3. **Review**:
   - Check for duplicates
   - Verify solution works
   - Ensure reusability
   - Tag appropriately

## Categories in Detail 🗂️
1. **Component Development**: Component architecture, prop management, state handling, and event systems.

2. **TypeScript Implementation**: Type definitions, interface design, generic usage, and type guards.

3. **Error Resolution**: Bug patterns, debug strategies, error prevention, and recovery methods.

4. **Performance Optimization**: Load time, runtime speed, memory usage, and network efficiency.

5. **Security Practices**: Data protection, input validation, authentication, and authorization.

6. **Accessibility Standards**: ARIA usage, keyboard nav, screen readers, and color contrast.

7. **Code Organization**: File structure, naming patterns, module design, and code reuse.

8. **Testing Strategies**: Unit tests, integration tests, E2E testing, and test patterns.

-----------------SCRATCHPAD RULES-----------------

# Scratchpad rules `@scratchpad.md`
The scratchpad serves as a phase-specific task tracker and implementation planner. Follow these rules:

1. **Phase Management**:
   - Track one phase at a time
   - Clear phase content only after phase completion
   - Transfer completed phase to `/docs/phases/PHASE-X-COMPLETED.md`
   - Start fresh for each new phase

2. **Documentation Transfer Process**:
   a. When phase is complete:
      - AI suggests documentation transfer
      - Creates comprehensive PHASE-X-COMPLETED.md
      - Organizes content into detailed tables and sections
      - Includes all implementations, decisions, and learnings
   b. After transfer:
      - Clear scratchpad of completed phase content
      - Prepare structure for next phase
      - Maintain mode system header

3. **Mode System**:
   - Keep Line 1 mode system types
   - Use Implementation Type for new features
   - Use Bug Fix Type for debugging
   - Track confidence levels and progress

4. **Progress Tracking**:
   - Use standardized markers [X], [-], [ ]
   - Update progress in real-time
   - Link to relevant memories
   - Track confidence scores

-----------PROJECT REQUIREMENTS RULES--------------
# Project Requirements rules `@docs/project-requirements.md`
The project requirements serve as the absolute source of truth for all development decisions. Follow these strict rules:

1. **Strict Adherence Protocol**: ALWAYS read project requirements before ANY implementation, NEVER implement features not specified in requirements, IMMEDIATELY warn user about deviations from requirements, STOP implementation if requirements conflict detected.

2. **Warning System**: Format `⚠️ WARNING: [Category] - [Detailed explanation of the issue]` with categories including ALIGNMENT (implementation deviations), RESTRICTION (restricted file modifications), DEPENDENCY (non-approved dependencies), ARCHITECTURE (structure deviations), and SCOPE (exceeding defined scope).

3. **Implementation Checklist**: ✅ Verify feature in project requirements, check implementation phase alignment, validate technical stack compliance, confirm architectural guidelines, review security requirements, and check performance implications.

4. **Restricted Operations**: DO NOT modify project requirements file, implement features from future phases, add unauthorized dependencies, change core architectural decisions, or bypass security requirements.

5. **Change Management**: Document ALL deviations from requirements, require explicit user approval for exceptions, track technical debt from compromises, and update documentation for approved changes.

6. **Quality Gates**: Requirements alignment check, phase compatibility verification, technical stack validation, security compliance review, and performance impact assessment.

7. **Warning Triggers**: Must warn user when implementation deviates from requirements, attempting to access restricted files, adding non-approved dependencies, modifying core architecture, implementing future phase features, bypassing security measures, exceeding phase scope, breaking established patterns, or compromising performance standards.

8. **Warning Format**:
   ```
   ⚠️ WARNING: [Category]
   - Issue: [Clear description of the problem]
   - Impact: [Potential consequences]
   - Requirement: [What the project requires]
   - Suggestion: [How to align with requirements]
   ```

9. **Enforcement Actions**: Handle deviations through Minor (warn user, suggest corrections, continue with caution), Major (block implementation, require user confirmation, document decision), and Critical (stop immediately, require replanning, update documentation) actions.

10. **Documentation Requirements**: Document all requirement checks, track approved deviations, maintain decision log, update related documentation, and cross-reference with memories.

# Documentations of PHASE-* on /docs/phases directory
Each phase completion requires:
1. Comprehensive documentation in `/docs/phases/PHASE-X-COMPLETED.md`
2. Tables and sections for:
   - Implemented components
   - Technical decisions
   - Code examples
   - Best practices
   - Lessons learned
3. Clear phase objectives and achievements
4. Links to relevant memories and lessons
